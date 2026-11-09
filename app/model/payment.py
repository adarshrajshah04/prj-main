from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    DateTime,
    Date
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class PaymentTable(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # Booking successful payment ke baad link hogi
    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=True,
        unique=True
    )

    # Property and booking details
    property_id = Column(
        Integer,
        ForeignKey("properties.id"),
        nullable=True
    )

    check_in = Column(Date, nullable=True)
    check_out = Column(Date, nullable=True)
    guests = Column(Integer, nullable=True)

    # Razorpay details
    razorpay_order_id = Column(
        String(100),
        unique=True,
        nullable=False
    )

    razorpay_payment_id = Column(
        String(100),
        unique=True,
        nullable=True
    )

    razorpay_signature = Column(
        String(256),
        nullable=True
    )

    amount = Column(Numeric(10, 2), nullable=False)

    status = Column(
        String(20),
        default="created",
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user = relationship(
        "UserTable",
        back_populates="payments"
    )

    booking = relationship(
        "BookingTable",
        back_populates="payment"
    )

    property = relationship("PropertyTable")