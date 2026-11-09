
import json
from pathlib import Path

from app.database import sessionLocal
from app.model import (
    UserTable,
    CategoryTable,
    PropertyTable,
    BookingTable,
    PaymentTable
)

JSON_FILE = (
    Path(__file__).parent
    / "data"
    / "escaperentals_properties_36.json"
)


def delete_old_properties():
    db = sessionLocal()

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            properties_data = json.load(file)

        property_names = [item["name"] for item in properties_data]

        old_properties = db.query(PropertyTable).filter(
            PropertyTable.name.in_(property_names)
        ).all()

        # Safety: booked properties ko delete nahi karna
        booked_properties = [
            prop.name for prop in old_properties if prop.bookings
        ]

        if booked_properties:
            print("Deletion cancelled. These properties have bookings:")
            for name in booked_properties:
                print(name)
            return

        for prop in old_properties:
            db.delete(prop)

        db.commit()

        print(f"Deleted successfully: {len(old_properties)} properties")

    except Exception as error:
        db.rollback()
        print("Error:", error)

    finally:
        db.close()


if __name__ == "__main__":
    delete_old_properties()
