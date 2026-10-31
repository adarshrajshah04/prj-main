import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_welcome_email(to_email: str, first_name: str):
    message = EmailMessage()
    message["Subject"] = "Welcome to EscapeRentals!"
    message["From"] = os.getenv("SMTP_EMAIL")
    message["To"] = to_email

    message.set_content(
        f"""Hi {first_name},

Welcome to EscapeRentals!

Your account has been successfully created.
We're happy to have you with us.

Enjoy your stay!

Regards,
EscapeRentals Team
"""
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(
            os.getenv("SMTP_EMAIL"),
            os.getenv("SMTP_PASSWORD")
        )
        server.send_message(message)