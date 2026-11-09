from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float,Boolean,JSON
from sqlalchemy.orm import relationship
from app.database import Base




class PropertyTable(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False
    )

    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=False)
    price_per_night = Column(Float, nullable=False)
    guest_capacity = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    cover_image = Column(String(255), nullable=True)
    images = Column(JSON, nullable=True, default=list)
    
    # latitude = Column(Float, nullable=True)
    # longitude = Column(Float, nullable=True)

    category = relationship(
        "CategoryTable",
        back_populates="properties"
    )
    
    bookings = relationship(
    "BookingTable",
    back_populates="property",
    cascade="all, delete-orphan"
    
    )
    
    reviews = relationship(
    "ReviewTable",
    back_populates="property",
    cascade="all, delete-orphan"
)
    
    wishlists = relationship(
    "WishlistTable",
    back_populates="property",
    cascade="all, delete-orphan"
)