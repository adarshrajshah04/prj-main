from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class UserTable(Base):
    __tablename__="users"
    
    id=Column(Integer,primary_key=True,nullable=False)
    first_name=Column(String(50),nullable=False)
    last_name=Column(String(50),nullable=False)
    email=Column(String(256),unique=True,nullable=False)
    contact_No=Column(String(15),unique=True,nullable=False)
    profile_image = Column(String(500), nullable=True)
    password=Column(String(256),nullable=False)
    is_admin=Column(Boolean,default=False,nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    bookings = relationship(
    "BookingTable",
    back_populates="user")
    
    payments = relationship(
    "PaymentTable",
    back_populates="user")
    
    reviews = relationship(
    "ReviewTable",
    back_populates="user",
    cascade="all, delete-orphan"
    )
    wishlists = relationship(
    "WishlistTable",
    back_populates="user",
    cascade="all, delete-orphan"
    )
