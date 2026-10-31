from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.model.booking import BookingTable
from app.model.properties import PropertyTable
from app.model.user import UserTable

from app.schemas.booking import BookingCreate, BookingResponse

from app.utils.auth import get_current_user, get_admin_user


router = APIRouter(
    prefix="/booking",
    tags=["Booking"]
)


# READ: Logged-in user ki apni bookings
@router.get("/my-bookings", response_model=list[BookingResponse])
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    bookings = db.query(BookingTable).filter(
        BookingTable.user_id == current_user.id
    ).all()

    return bookings


# READ: Admin sabhi bookings dekh sakta hai
@router.get("/all", response_model=list[BookingResponse])
def get_all_bookings(
    db: Session = Depends(get_db),
    current_admin: UserTable = Depends(get_admin_user)
):
    return db.query(BookingTable).all()


# READ: Specific booking
@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    booking = db.query(BookingTable).filter(
        BookingTable.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if not current_user.is_admin and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access this booking"
        )

    return booking


# UPDATE: User apni booking update kar sakta hai
@router.put("/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: int,
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    booking = db.query(BookingTable).filter(
        BookingTable.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if not current_user.is_admin and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot update this booking"
        )

    # Payment-confirmed bookings ke liye direct date/property update
    # allow nahi karna chahiye. Rescheduling ka separate payment/
    # availability workflow banega.
    raise HTTPException(
        status_code=400,
        detail="Booking updates must go through the rescheduling process"
    )


# DELETE: User apni booking delete kar sakta hai
@router.delete("/{booking_id}")
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    booking = db.query(BookingTable).filter(
        BookingTable.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if not current_user.is_admin and booking.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot delete this booking"
        )

    # Payment/refund rules decide hone tak paid booking
    # ko permanently delete nahi karenge.
    raise HTTPException(
        status_code=400,
        detail="Please use the booking cancellation process"
    )
    
    
@router.post(
    "/create",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED
)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Check property exists
    property_data = db.query(PropertyTable).filter(
        PropertyTable.id == booking.property_id,
        PropertyTable.is_active == True
    ).first()

    if not property_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Check dates
    if booking.check_in < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-in date cannot be in the past"
        )

    if booking.check_out <= booking.check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-out must be after check-in"
        )

    # Check guests
    if booking.guests <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guests must be at least 1"
        )

    # Further booking and payment logic will be added here.