from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class NotificationTable(Base):
    __tablename__ = "Notification"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    username = Column(String(100), nullable=False)

    action = Column(String(20), nullable=False)
    # CREATE, UPDATE, DELETE

    entity = Column(String(100), nullable=False)
    # Category, Property, Booking, Payment

    description = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )