from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from decimal import Decimal


class BookingCreate(BaseModel):
    property_id: int
    check_in: date
    check_out: date
    guests: int


class BookingResponse(BaseModel):
    id: int
    user_id: int
    property_id: int
    check_in: date
    check_out: date
    guests: int
    total_price: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)