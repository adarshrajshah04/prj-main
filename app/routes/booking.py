from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.model.booking import BookingTable
from app.model.user import UserTable

from app.schemas.booking import BookingCreate, BookingResponse

from app.utils.auth import get_current_user, get_admin_user


router = APIRouter(
    prefix="/booking",
    tags=["Booking"]
)


# READ: Logged-in user ki apni bookings
@router.get("/", response_model=list[BookingResponse])
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):
    bookings = db.query(BookingTable).filter(
        BookingTable.user_id == current_user.id
    ).all()

    return bookings


# All booking for only admin
@router.get("/all", response_model=list[BookingResponse])
def get_all_bookings(
    db: Session = Depends(get_db),
    current_admin: UserTable = Depends(get_admin_user)
):
    return db.query(BookingTable).all()

# # create booking
# @router.post("/")
# def create_booking(
#     booking: BookingCreate,
#     current_user: UserTable = Depends(get_current_user)
# ):
#     raise HTTPException(
#         status_code=status.HTTP_409_CONFLICT,
#         detail="Bookings require payment. Create a Razorpay order at /payment/create-order and verify it at /payment/verify."
#     )


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