import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_booking_confirmation_email(
    to_email,
    customer_name,
    property_name,
    booking_id,
    check_in,
    check_out,
    amount,
    order_id
):
    msg = EmailMessage()

    msg["Subject"] = "Your EscapeRentals Booking is Confirmed!"
    msg["From"] = os.getenv("EMAIL_HOST_USER")
    msg["To"] = to_email

    msg.set_content(f"""
Dear {customer_name},

Thank you for choosing EscapeRentals!

Your booking has been successfully confirmed.

BOOKING DETAILS
-------------------------

Booking ID: {booking_id}
Property: {property_name}
Check-in Date: {check_in}
Check-out Date: {check_out}
Total Amount: Rs. {amount:.2f}
Payment Status: Successful
Razorpay Order ID: {order_id}

Thank you for booking with EscapeRentals!

We look forward to hosting you.
Have a wonderful stay!

Regards,
EscapeRentals Team
""")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()

        server.login(
            os.getenv("EMAIL_HOST_USER"),
            os.getenv("EMAIL_HOST_PASSWORD")
        )

        server.send_message(msg)