from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import date, datetime
from typing import Optional


# Razorpay Order Create Request
class PaymentCreate(BaseModel):
    property_id: int
    check_in: date
    check_out: date
    guests: int


# Razorpay Order Response
class PaymentOrderResponse(BaseModel):
    payment_id: int
    razorpay_order_id: str
    razorpay_key_id: str
    amount: int
    currency: str
    status: str


# Payment Verification Request
class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# Payment Response
class PaymentResponse(BaseModel):
    id: int
    user_id: int
    booking_id: Optional[int] = None
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    amount: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)