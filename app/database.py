from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import declarative_base,sessionmaker
import os
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from .env")

engine=create_engine(DATABASE_URL)

sessionLocal=sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_payment_schema():
    if "payments" not in inspect(engine).get_table_names():
        return

    existing_columns = {
        column["name"] for column in inspect(engine).get_columns("payments")
    }
    missing_columns = {
        "property_id": "INTEGER REFERENCES properties(id)",
        "check_in": "DATE",
        "check_out": "DATE",
        "guests": "INTEGER",
    }

    with engine.begin() as connection:
        for column_name, column_definition in missing_columns.items():
            if column_name not in existing_columns:
                connection.exec_driver_sql(
                    f"ALTER TABLE payments ADD COLUMN "
                    f"{column_name} {column_definition}"
                )