from fastapi import APIRouter,HTTPException,Depends,UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.model.category import CategoryTable
from app.schemas.category import *
from app.utils.auth import *
from pathlib import Path
import shutil
import uuid
from app.utils.notification import create_notification

router = APIRouter(
    prefix="/categories",
    tags=["Categories Management"]
)

UPLOAD_DIR = Path("uploads/categories")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# get category all
@router.get("/")
def allCategory(db:Session=Depends(get_db)):
    
    all_Category=db.query(CategoryTable).all()
    
    return{
        "message":"All categories",
        "data":all_Category
    }
    

# create category
# @router.post("/",response_model=CategoryResponse)
# def createCategory(
#     data:CategoryCreate,
#     db:Session=Depends(get_db),
#     current_admin=Depends(get_admin_user)
#     ):
#     checkCategory=db.query(CategoryTable).filter(CategoryTable.name==data.name).first()
    
#     if checkCategory is not None:
#         raise HTTPException(
#             status_code=409,
#             detail=f"{data.name} this category name is exist"
#         )
#     # sending the date into the model
#     new_category = CategoryTable(**data.model_dump())
    
#     db.add(new_category)
#     db.commit()
#     db.refresh(new_category)
    
#     return new_category


@router.post("/", response_model=CategoryResponse)
def createCategory(
    name: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    checkCategory = db.query(CategoryTable).filter(
        CategoryTable.name == name
    ).first()

    if checkCategory:
        raise HTTPException(status_code=409, detail="Category already exists")

    extension = Path(image.filename).suffix.lower()

    if extension not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    filename = f"{uuid.uuid4()}{extension}"
    image_path = UPLOAD_DIR / filename

    with image_path.open("wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    new_category = CategoryTable(
        name=name,
        description=description,
        image=f"uploads/categories/{filename}"
    )

    db.add(new_category)
    db.commit()
    
    # sending the notification
    create_notification(
    current_user=current_admin,
    action="CREATE",
    entity="Category",
    description=f"Category '{new_category.name}' created")
    
    
    db.refresh(new_category)

    return new_category


# update category 
@router.put("/{category_id}",response_model=CategoryResponse)
def updateCategory(
    category_id:int,
    data:CategoryUpdate,
    db:Session=Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    
    update_Category=db.query(CategoryTable).filter(CategoryTable.id==category_id).first()
    
    if not update_Category:
        raise HTTPException(
            status_code=404,
            detail=f"{category_id} category id is not found"
        )
    
    update_Category.name=data.name
    update_Category.description=data.description
    # update_Category.image=data.image
    update_Category.is_active=data.is_active
    
    db.commit()
    
    # sending the notification
    create_notification(
        current_user=current_admin,
        action="Update",
        entity="Category",
        description=f"Category '{update_Category.name}' updated")
    
    db.refresh(update_Category)
    
        
    return update_Category
    

# delete data
@router.delete("/{category_id}")
def delete_property(
    category_id:int,
    db:Session=Depends(get_db),
    current_admin=Depends(get_admin_user)
    ):
    
    delete_data=db.query(CategoryTable).filter(CategoryTable.id==category_id).first()
        
    if not delete_data:
        raise HTTPException(
            status_code=404,
            detail=f"{category_id} category id is not found"
        )
        
    db.delete(delete_data)
    db.commit()
    create_notification(
            current_user=current_admin,
            action="Delete",
            entity="Category",
            description=f"Category '{delete_data.name}' Deleted")
    
    
    return{
        "message":f"{delete_data.name} was deleted successfully"
    }
    




    