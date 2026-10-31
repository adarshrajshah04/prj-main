import os
import razorpay

from dotenv import load_dotenv

load_dotenv()


RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise ValueError("Razorpay API credentials are missing from .env")


# Initialize Razorpay Client
client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)


# Create Razorpay Order
def create_razorpay_order(amount: int, receipt: str):
    order_data = {
        "amount": amount,
        "currency": "INR",
        "receipt": receipt,
        "payment_capture": 1
    }

    order = client.order.create(data=order_data)

    return order


# Verify Razorpay Payment
def verify_razorpay_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str
):
    payment_data = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature
    }

    try:
        client.utility.verify_payment_signature(payment_data)
        return True

    except razorpay.errors.SignatureVerificationError:
        return False

# Fetch Razorpay Payment Details
def get_razorpay_payment(razorpay_payment_id: str):

    payment = client.payment.fetch(razorpay_payment_id)

    return payment