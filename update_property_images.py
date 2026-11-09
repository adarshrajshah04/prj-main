
import json
from pathlib import Path

from app.database import sessionLocal
from app.model import PropertyTable

JSON_FILE = (
    Path(__file__).parent
    / "data"
    / "escaperentals_properties_36.json"
)


def update_property_images():
    db = sessionLocal()

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            properties_data = json.load(file)

        updated = 0
        not_found = []

        for item in properties_data:
            property_obj = (
                db.query(PropertyTable)
                .filter(PropertyTable.name == item["name"])
                .first()
            )

            if not property_obj:
                not_found.append(item["name"])
                continue

            property_obj.cover_image = item["cover_image"]
            property_obj.images = item["images"]

            updated += 1

        db.commit()

        print(f"Updated properties: {updated}")
        print(f"Not found: {len(not_found)}")

        if not_found:
            print("Missing properties:", not_found)

    except Exception as error:
        db.rollback()
        print("Error:", error)

    finally:
        db.close()


if __name__ == "__main__":
    update_property_images()
