from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class CategoryTable(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)
    image = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    properties = relationship(
        "PropertyTable",
        back_populates="category",
        cascade="all, delete-orphan"
    )