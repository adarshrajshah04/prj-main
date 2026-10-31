
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Date,
    DateTime,
    String,
    Numeric
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class BookingTable(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    property_id = Column(
        Integer,
        ForeignKey("properties.id"),
        nullable=False
    )

    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)

    guests = Column(Integer, nullable=False)

    total_price = Column(Numeric(10, 2), nullable=False)

    status = Column(
        String(20),
        default="pending",
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    
    payment = relationship(
    "PaymentTable",
    back_populates="booking",
    uselist=False
)

    user = relationship(
    "UserTable",
    back_populates="bookings"
    )

    property = relationship(
        "PropertyTable",
        back_populates="bookings"
    )
    
    