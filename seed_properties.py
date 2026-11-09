
import json
from pathlib import Path

from app.database import sessionLocal
# Import all models before database queries
from app.model import (
    UserTable,
    CategoryTable,
    PropertyTable,
    BookingTable,
    PaymentTable
)
JSON_FILE = Path(__file__).parent / "data" / "escaperentals_properties_36.json"


def seed_properties():
    db = sessionLocal()

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            properties_data = json.load(file)

        added_count = 0
        skipped_count = 0

        for item in properties_data:

            # Check whether category exists
            category = db.query(CategoryTable).filter(
                CategoryTable.id == item["category_id"]
            ).first()

            if not category:
                print(
                    f"Category ID {item['category_id']} not found. "
                    f"Skipping: {item['name']}"
                )
                skipped_count += 1
                continue

            # Avoid inserting the same property again
            existing = db.query(PropertyTable).filter(
                PropertyTable.name == item["name"]
            ).first()

            if existing:
                print(f"Already exists: {item['name']}")
                skipped_count += 1
                continue

            property_obj = PropertyTable(
                category_id=item["category_id"],
                name=item["name"],
                description=item["description"],
                location=item["location"],
                price_per_night=item["price_per_night"],
                guest_capacity=item["guest_capacity"],
                is_active=item["is_active"],
                cover_image=item["cover_image"],
                images=item["images"]
            )

            db.add(property_obj)
            added_count += 1

        db.commit()

        print(f"Successfully added: {added_count}")
        print(f"Skipped: {skipped_count}")

    except Exception as error:
        db.rollback()
        print("Error while seeding properties:", error)

    finally:
        db.close()


if __name__ == "__main__":
    seed_properties()
