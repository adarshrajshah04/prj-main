from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class ReviewTable(Base):
    __tablename__ = "reviews"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "property_id",
            name="unique_user_property_review"
        ),
    )

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

    rating = Column(Integer, nullable=False)
    comment = Column(String(1000), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserTable", back_populates="reviews")
    property = relationship("PropertyTable", back_populates="reviews")