
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timedelta, timezone
import uuid
import logging

from app.database import get_db
from app.model.user import UserTable
from app.model.properties import PropertyTable
from app.model.payment import PaymentTable
from app.model.booking import BookingTable

from app.schemas.payment import (
    PaymentCreate,
    PaymentOrderResponse,
    PaymentVerify,
    PaymentResponse
)

from app.utils.auth import get_current_user
from app.utils.razorpay import (
    create_razorpay_order,
    verify_razorpay_payment,
    get_razorpay_payment,
    capture_razorpay_payment,
    RAZORPAY_KEY_ID
)

from fastapi import BackgroundTasks
from app.services.confirmation_mail import send_booking_confirmation_email
from app.utils.notification import create_notification


router = APIRouter(
    prefix="/payment",
    tags=["Payment"]
)

logger = logging.getLogger(__name__)
ORDER_EXPIRY = timedelta(minutes=30)


# CREATE RAZORPAY ORDER
@router.post(
    "/create-order",
    response_model=PaymentOrderResponse
)
def create_order(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):

    property_data = db.query(PropertyTable).filter(
        PropertyTable.id == payment_data.property_id,
        PropertyTable.is_active.is_(True)
    ).with_for_update().first()

    if not property_data:
        raise HTTPException(
            status_code=404,
            detail="Property not found"
        )

    if payment_data.check_in < date.today():
        raise HTTPException(
            status_code=400,
            detail="Check-in date cannot be in the past"
        )

    if payment_data.check_out <= payment_data.check_in:
        raise HTTPException(
            status_code=400,
            detail="Check-out date must be after check-in"
        )

    if payment_data.guests <= 0:
        raise HTTPException(
            status_code=400,
            detail="Guests must be at least 1"
        )

    if payment_data.guests > property_data.guest_capacity:
        raise HTTPException(
            status_code=400,
            detail="Guest capacity exceeded"
        )

    now = datetime.now(timezone.utc)

    existing_booking = db.query(BookingTable).filter(
        BookingTable.property_id == property_data.id,
        BookingTable.status == "confirmed",
        BookingTable.check_in < payment_data.check_out,
        BookingTable.check_out > payment_data.check_in
    ).first()

    if existing_booking:
        raise HTTPException(
            status_code=409,
            detail="Property is not available for these dates"
        )

    existing_order = db.query(PaymentTable).filter(
        PaymentTable.property_id == property_data.id,
        PaymentTable.status == "created",
        PaymentTable.created_at >= now - ORDER_EXPIRY,
        PaymentTable.check_in < payment_data.check_out,
        PaymentTable.check_out > payment_data.check_in
    ).first()

    if existing_order:
        raise HTTPException(
            status_code=409,
            detail="These dates are temporarily reserved while another payment is completed"
        )

    # Calculate total price on backend
    total_days = (
        payment_data.check_out - payment_data.check_in
    ).days

    total_price = (
        Decimal(str(property_data.price_per_night)) * total_days
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if total_price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Property price must be greater than zero"
        )

    amount = int(total_price * Decimal("100"))

    receipt = f"receipt_{uuid.uuid4().hex[:20]}"

    try:
        razorpay_order = create_razorpay_order(
        amount=amount,
        receipt=receipt
        )

        if (
            razorpay_order.get("amount") != amount
            or razorpay_order.get("currency") != "INR"
        ):
            raise HTTPException(
                status_code=502,
                detail="Razorpay returned an order with unexpected amount or currency"
            )

        payment = PaymentTable(
            user_id=current_user.id,
            property_id=property_data.id,
            check_in=payment_data.check_in,
            check_out=payment_data.check_out,
            guests=payment_data.guests,
            razorpay_order_id=razorpay_order["id"],
            amount=total_price,
            status="created"
        )
        db.add(payment)
        db.flush()

        booking = BookingTable(
            user_id=current_user.id,
            property_id=property_data.id,
            check_in=payment_data.check_in,
            check_out=payment_data.check_out,
            guests=payment_data.guests,
            total_price=total_price,
            status="pending"
        )
        db.add(booking)
        db.flush()

        payment.booking_id = booking.id
        db.commit()

        return PaymentOrderResponse(
            payment_id=payment.id,
            razorpay_order_id=razorpay_order["id"],
            razorpay_key_id=RAZORPAY_KEY_ID,
            amount=amount,
            currency="INR",
            status=payment.status
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        logger.exception("Could not create Razorpay order and booking reservation")
        raise HTTPException(
            status_code=500,
            detail="Unable to create payment order"
        ) from exc


# VERIFY PAYMENT AND CREATE BOOKING
@router.post(
    "/verify",
    response_model=PaymentResponse
)
def verify_payment(
    payment_data: PaymentVerify,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):

    payment = db.query(PaymentTable).filter(
        PaymentTable.razorpay_order_id == payment_data.razorpay_order_id,
        PaymentTable.user_id == current_user.id
    ).with_for_update().first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment order not found"
        )

    if payment.status == "success":
        if (
            payment.razorpay_payment_id == payment_data.razorpay_payment_id
            and payment.razorpay_signature == payment_data.razorpay_signature
        ):
            return payment
        raise HTTPException(status_code=409, detail="Payment order was already verified")

    if payment.status != "created":
        raise HTTPException(
            status_code=400,
            detail="Payment order is not valid for verification"
        )

    if (
        payment.property_id is None
        or payment.check_in is None
        or payment.check_out is None
        or payment.guests is None
    ):
        raise HTTPException(
            status_code=409,
            detail="This order was created before booking details were stored. Please create a new payment order."
        )

    # Verify Razorpay signature
    is_verified = verify_razorpay_payment(
        razorpay_order_id=payment_data.razorpay_order_id,
        razorpay_payment_id=payment_data.razorpay_payment_id,
        razorpay_signature=payment_data.razorpay_signature
    )

    if not is_verified:
        payment.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Payment signature verification failed"
        )

    try:
        # Fetch actual payment details from Razorpay
        razorpay_payment = get_razorpay_payment(
            payment_data.razorpay_payment_id
        )

        # Verify order, amount and currency before capturing an authorized payment.
        expected_amount = int(payment.amount * 100)

        if (
            razorpay_payment.get("order_id") != payment.razorpay_order_id
            or razorpay_payment.get("amount") != expected_amount
            or razorpay_payment.get("currency") != "INR"
        ):
            raise HTTPException(
                status_code=400,
                detail="Razorpay payment details do not match"
            )

        if razorpay_payment.get("status") == "authorized":
            razorpay_payment = capture_razorpay_payment(
                payment_data.razorpay_payment_id,
                expected_amount
            )

        if razorpay_payment.get("status") != "captured":
            raise HTTPException(
                status_code=400,
                detail="Razorpay payment is not captured"
            )

        if payment.booking_id is None:
            booking = BookingTable(
                user_id=payment.user_id,
                property_id=payment.property_id,
                check_in=payment.check_in,
                check_out=payment.check_out,
                guests=payment.guests,
                total_price=payment.amount,
                status="pending"
            )
            db.add(booking)
            db.flush()
            payment.booking_id = booking.id
        else:
            booking = db.query(BookingTable).filter(
                BookingTable.id == payment.booking_id,
                BookingTable.user_id == current_user.id
            ).with_for_update().first()

            if not booking:
                raise HTTPException(
                    status_code=409,
                    detail="Booking reservation for this payment was not found"
                )

        db.query(PropertyTable).filter(
            PropertyTable.id == payment.property_id
        ).with_for_update().first()

        # Check property availability again
        existing_booking = db.query(BookingTable).filter(
            BookingTable.property_id == payment.property_id,
            BookingTable.status == "confirmed",
            BookingTable.id != booking.id,
            BookingTable.check_in < payment.check_out,
            BookingTable.check_out > payment.check_in
        ).first()

        if existing_booking:
            payment.razorpay_payment_id = payment_data.razorpay_payment_id
            payment.razorpay_signature = payment_data.razorpay_signature
            payment.status = "refund_required"
            booking.status = "cancelled"
            db.commit()
            raise HTTPException(
                status_code=409,
                detail="Payment was captured but the booking could not be confirmed. A refund is required; contact support with the payment ID."
            )

        booking.status = "confirmed"
        payment.razorpay_payment_id = payment_data.razorpay_payment_id
        payment.razorpay_signature = payment_data.razorpay_signature
        payment.status = "success"

        db.commit()
        db.refresh(payment)
        create_notification(
            current_user=current_user,
            action="Booking ",
            entity="Payment",
            description=f"booking '{booking.property_id.name}' ")
        
        property_obj = db.query(PropertyTable).filter(
        PropertyTable.id == payment.property_id
        ).first()

        if property_obj:
            background_tasks.add_task(
                send_booking_confirmation_email,
                to_email=current_user.email,
                customer_name=current_user.first_name,
                property_name=property_obj.name,
                booking_id=booking.id,
                check_in=str(payment.check_in),
                check_out=str(payment.check_out),
                amount=float(payment.amount) / 100,
                order_id=payment.razorpay_order_id
            )

        return payment

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        logger.exception("Payment verification or booking confirmation failed")
        raise HTTPException(
            status_code=500,
            detail="Payment verification or booking creation failed"
        ) from exc


