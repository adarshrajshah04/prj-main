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
from typing import List
from decimal import Decimal
from app.utils.notification import create_notification


router = APIRouter(
    prefix="/properties",
    tags=["Property Management"]
)

UPLOAD_DIR = Path("uploads/properties")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# get all product
@router.get("/")
def all_properties(db: Session = Depends(get_db)):
    all_data=db.query(PropertyTable).all()
    
    return{
        "message":"All property data",
        "data":all_data
    }
# Get single data
@router.get("/{property_id}",response_model=PropertyResponse)
def singleProperty(property_id:int,db: Session = Depends(get_db)):
    data=db.query(PropertyTable).filter(PropertyTable.id==property_id).first()
    
    if data is None:
        raise HTTPException(
            status_code=404,
            detail="Property not found"
        )
    return data

# get single category data
@router.get("/category/{category_id}")
def allCategoryData(category_id:int,db: Session = Depends(get_db)):
    
    all_data=db.query(PropertyTable).filter(PropertyTable.category_id==category_id).all()
    
    if all_data is None:
        raise HTTPException(
            status_code=404,
            detail="category not found"
        )
        
    return{
            "message":"All property data",
            "data":all_data
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
    property_id:int,
    data:PropertyUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
    ):
    
    update_data=db.query(PropertyTable).filter(PropertyTable.id==property_id).first()
    
    if not update_data:
        raise HTTPException(
            status_code=404,
            detail=f"{property_id} property id is not found"
        )
    
    update_data.name=data.name
    update_data.description=data.description
    update_data.location=data.location
    update_data.price_per_night=data.price_per_night
    update_data.guest_capacity=data.guest_capacity
    update_data.is_active=data.is_active
    
    db.commit()
    # sending the notification
    create_notification(
        current_user=current_admin,
        action="Update",
        entity="Properties",
        description=f"Category '{update_data.name}' Updated")
        
    db.refresh(update_data)
    
    return{
        "message":f"{update_data.name} is updated successfully",
        "data":data
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


