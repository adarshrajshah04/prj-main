from fastapi import APIRouter, Depends, HTTPException,Form, File, UploadFile
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.properties import *
from app.model.category import *
from app.schemas.properties import *
from app.utils.auth import get_admin_user
from pathlib import Path
import shutil
import uuid
from typing import List,Optional
from decimal import Decimal
from app.utils.notification import create_notification
from app.model.review import ReviewTable
from sqlalchemy import func

router = APIRouter(
    prefix="/properties",
    tags=["Property Management"]
)

BASE_DIR = Path.cwd()

UPLOAD_DIR = BASE_DIR / "uploads" / "properties"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Get all properties
@router.get("/")
def all_properties(db: Session = Depends(get_db)):

    all_data = db.query(PropertyTable).all()

    data = []

    for property in all_data:

        rating_data = db.query(
            func.avg(ReviewTable.rating),
            func.count(ReviewTable.id)
        ).filter(
            ReviewTable.property_id == property.id
        ).first()

        average_rating = rating_data[0] or 0
        total_reviews = rating_data[1] or 0

        data.append({
            "id": property.id,
            "category_id": property.category_id,
            "category_name": property.category.name if property.category else None,
            "name": property.name,
            "description": property.description,
            "location": property.location,
            "price_per_night": property.price_per_night,
            "guest_capacity": property.guest_capacity,
            "is_active": property.is_active,
            "cover_image": property.cover_image,
            "images": property.images or [],

            # Rating
            "rating": round(float(average_rating), 1),
            "total_reviews": total_reviews
        })

    return {
        "message": "All property data",
        "data": data
    }
    
    
    
    
# Get single data
@router.get("/{property_id}")
def singleProperty(property_id: int, db: Session = Depends(get_db)):

    sdata = db.query(PropertyTable).filter(
        PropertyTable.id == property_id
    ).first()

    if sdata is None:
        raise HTTPException(
            status_code=404,
            detail="Property not found"
        )
        
    rating_data = db.query(
    func.avg(ReviewTable.rating),
    func.count(ReviewTable.id)
    ).filter(
        ReviewTable.property_id == property_id
    ).first()

    average_rating = rating_data[0] or 0
    total_reviews = rating_data[1] or 0

    data = {
        "id": sdata.id,
        "category_id": sdata.category_id,
        "category_name": sdata.category.name,
        "name": sdata.name,
        "description": sdata.description,
        "location": sdata.location,
        "price_per_night": sdata.price_per_night,
        "guest_capacity": sdata.guest_capacity,
        "is_active": sdata.is_active,
        "cover_image": sdata.cover_image,
        "images": sdata.images or [],
        
        "rating": round(float(average_rating), 1),
        "total_reviews": total_reviews
    }

    return data

# get single category data
@router.get("/category/{category_id}")
def allCategoryData(category_id:int,db: Session = Depends(get_db)):
    
    all_data=db.query(PropertyTable).filter(PropertyTable.category_id==category_id).all()
    
    if not all_data:
        raise HTTPException(
            status_code=404,
            detail="category not found"
        )
        
    data = []

    for property in all_data:

        rating_data = db.query(
            func.avg(ReviewTable.rating),
            func.count(ReviewTable.id)
        ).filter(
            ReviewTable.property_id == property.id
        ).first()

        average_rating = rating_data[0] or 0
        total_reviews = rating_data[1] or 0

        data.append({
            "id": property.id,
            "category_id": property.category_id,
            "category_name": property.category.name if property.category else None,
            "name": property.name,
            "description": property.description,
            "location": property.location,
            "price_per_night": property.price_per_night,
            "guest_capacity": property.guest_capacity,
            "is_active": property.is_active,
            "cover_image": property.cover_image,
            "images": property.images or [],

            # Rating
            "rating": round(float(average_rating), 1),
            "total_reviews": total_reviews
        })

    return {
        "message": "All property data",
        "data": data
    }
    
    
# create Property

@router.post("/", response_model=PropertyResponse)
def createProperty(
    category_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    price_per_night: Decimal = Form(...),
    guest_capacity: int = Form(...),
    cover_image: UploadFile = File(...),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    category = db.query(CategoryTable).filter(
        CategoryTable.id == category_id,
        CategoryTable.is_active == True
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Active category not found"
        )

    allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]

    def save_image(file):
        extension = Path(file.filename).suffix.lower()

        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail="Invalid image format"
            )

        filename = f"{uuid.uuid4()}{extension}"
        file_path = UPLOAD_DIR / filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"uploads/properties/{filename}"

    cover_path = save_image(cover_image)
    gallery_paths = [save_image(img) for img in images]

    new_property = PropertyTable(
        category_id=category_id,
        name=name,
        description=description,
        location=location,
        price_per_night=price_per_night,
        guest_capacity=guest_capacity,
        cover_image=cover_path,
        images=gallery_paths
    )

    db.add(new_property)
    db.commit()
    # sending the notification
    create_notification(
            current_user=current_admin,
            action="Create",
            entity="Properties",
            description=f"Category '{new_property.name}' Created")
    db.refresh(new_property)

    return new_property



# Update model
@router.put("/{property_id}")
def updateProperty(
    property_id: int,
    category_id: int = Form(...),

    name: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    price_per_night: float = Form(...),
    guest_capacity: int = Form(...),
    is_active: bool = Form(...),

    cover_image: Optional[UploadFile] = File(default=None),
    images: Optional[List[UploadFile]] = File(default=None),

    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):

    update_data = db.query(PropertyTable).filter(
        PropertyTable.id == property_id
    ).first()

    if not update_data:
        raise HTTPException(
            status_code=404,
            detail=f"{property_id} property id is not found"
        )

    # Update normal fields
    update_data.name = name
    update_data.description = description
    update_data.location = location
    update_data.price_per_night = price_per_night
    update_data.guest_capacity = guest_capacity
    update_data.is_active = is_active
    update_data.category_id=category_id

    # Allowed image formats
    allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]

    # Update cover image
    if cover_image and cover_image.filename:

        extension = Path(cover_image.filename).suffix.lower()

        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail="Invalid cover image format"
            )

        filename = f"{uuid.uuid4()}{extension}"
        image_path = UPLOAD_DIR / filename

        with image_path.open("wb") as buffer:
            shutil.copyfileobj(cover_image.file, buffer)

        # Delete old cover image
        if update_data.cover_image:
            old_path = Path(update_data.cover_image)

            if not old_path.is_absolute():
                old_path = BASE_DIR / old_path

            if old_path.exists():
                old_path.unlink()

        update_data.cover_image = f"uploads/properties/{filename}"

    # Update gallery images
    new_images = [
        img for img in (images or [])
        if img.filename
    ]

    if new_images:

        # Validate all images before saving
        for img in new_images:
            extension = Path(img.filename).suffix.lower()

            if extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid image format: {img.filename}"
                )

        new_image_paths = []

        for img in new_images:

            extension = Path(img.filename).suffix.lower()
            filename = f"{uuid.uuid4()}{extension}"
            image_path = UPLOAD_DIR / filename

            with image_path.open("wb") as buffer:
                shutil.copyfileobj(img.file, buffer)

            new_image_paths.append(
                f"uploads/properties/{filename}"
            )

        # Delete old gallery images
        for old_image in update_data.images or []:

            old_path = Path(old_image)

            if not old_path.is_absolute():
                old_path = BASE_DIR / old_path

            if old_path.exists():
                old_path.unlink()

        update_data.images = new_image_paths

    db.commit()

    create_notification(
        current_user=current_admin,
        action="UPDATE",
        entity="Properties",
        description=f"Property '{update_data.name}' updated"
    )

    db.refresh(update_data)

    return {
        "message": f"{update_data.name} updated successfully",
        "data": update_data
    }

# delete data
@router.delete("/{property_id}")
def delete_property(
    property_id:int,
    db:Session=Depends(get_db),
    current_admin=Depends(get_admin_user)
    ):
    
    delete_data=db.query(PropertyTable).filter(PropertyTable.id==property_id).first()
        
    if not delete_data:
        raise HTTPException(
            status_code=404,
            detail=f"{property_id} property id is not found"
        )
    
    # sending the notification
    create_notification(
        current_user=current_admin,
        action="Delete",
        entity="Properties",
        description=f"Category '{delete_data.name}' Deleted")
            
    db.delete(delete_data)
    db.commit()
    
    
    return{
            "message":f"{delete_data.name} is deleted successfully",
        }


