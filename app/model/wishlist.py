from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class WishlistTable(Base):
    __tablename__ = "wishlists"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "property_id",
            name="unique_user_wishlist_property"
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

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserTable", back_populates="wishlists")
    property = relationship("PropertyTable", back_populates="wishlists")