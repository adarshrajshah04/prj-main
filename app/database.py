from sqlalchemy import create_engine
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