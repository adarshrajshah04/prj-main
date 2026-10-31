
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
import uuid

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
    RAZORPAY_KEY_ID
)


router = APIRouter(
    prefix="/payment",
    tags=["Payment"]
)


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
    ).first()

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

    # Check existing confirmed bookings
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

    amount = int(total_price * 100)

    receipt = f"receipt_{uuid.uuid4().hex[:20]}"

    try:
        razorpay_order = create_razorpay_order(
            amount=amount,
            receipt=receipt
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
        db.commit()
        db.refresh(payment)

        return PaymentOrderResponse(
            payment_id=payment.id,
            razorpay_order_id=razorpay_order["id"],
            razorpay_key_id=RAZORPAY_KEY_ID,
            amount=payment.amount,
            currency="INR",
            status=payment.status
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to create payment order"
        )


# VERIFY PAYMENT AND CREATE BOOKING
@router.post(
    "/verify",
    response_model=PaymentResponse
)
def verify_payment(
    payment_data: PaymentVerify,
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
        raise HTTPException(
            status_code=400,
            detail="Payment already verified"
        )

    if payment.status != "created":
        raise HTTPException(
            status_code=400,
            detail="Payment order is not valid for verification"
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

        # Verify order, amount, currency and captured status
        expected_amount = int(payment.amount * 100)

        if (
            razorpay_payment["order_id"] != payment.razorpay_order_id
            or razorpay_payment["amount"] != expected_amount
            or razorpay_payment["currency"] != "INR"
            or razorpay_payment["status"] != "captured"
        ):
            raise HTTPException(
                status_code=400,
                detail="Razorpay payment details do not match"
            )

        # Check property availability again
        existing_booking = db.query(BookingTable).filter(
            BookingTable.property_id == payment.property_id,
            BookingTable.status == "confirmed",
            BookingTable.check_in < payment.check_out,
            BookingTable.check_out > payment.check_in
        ).first()

        if existing_booking:
            raise HTTPException(
                status_code=409,
                detail="Property is no longer available. Payment requires refund."
            )

        # Create booking only after successful payment
        booking = BookingTable(
            user_id=payment.user_id,
            property_id=payment.property_id,
            check_in=payment.check_in,
            check_out=payment.check_out,
            guests=payment.guests,
            total_price=payment.amount,
            status="confirmed"
        )

        db.add(booking)
        db.flush()

        # Link booking with payment
        payment.booking_id = booking.id
        payment.razorpay_payment_id = payment_data.razorpay_payment_id
        payment.razorpay_signature = payment_data.razorpay_signature
        payment.status = "success"

        db.commit()
        db.refresh(payment)

        return payment

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Payment verification or booking creation failed"
        )
