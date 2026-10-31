from pydantic import BaseModel, Field
from decimal import Decimal


# Create Property
class PropertyCreate(BaseModel):
    category_id: int
    name: str=Field( min_length=2, max_length=150)
    description: str
    location: str=Field( min_length=2, max_length=255)
    price_per_night: Decimal
    guest_capacity: int


# Update Property   
class PropertyUpdate(BaseModel):
    category_id: int 
    name: str  = Field( min_length=2, max_length=150)
    description: str 
    location: str  = Field( min_length=2, max_length=255)
    price_per_night: Decimal  = Field(gt=0, max_digits=10, decimal_places=2)
    guest_capacity: int  = Field( gt=0)
    is_active: bool 


# Property Response
class PropertyResponse(BaseModel):
    id: int
    category_id: int
    name: str
    description: str | None
    location: str
    price_per_night: Decimal
    guest_capacity: int
    is_active: bool
    cover_image: str | None = None
    images: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}