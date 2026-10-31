from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form
)
from sqlalchemy.orm import Session
from app.schemas.users import *
from app.model.user import *
from app.database import get_db
from passlib.context import CryptContext
from pathlib import Path
import shutil
import uuid
from app.services.registration_mail import send_welcome_email
from fastapi import BackgroundTasks
from app.utils.jwt import create_access_token
from fastapi.security import HTTPBearer
from app.utils.auth import get_admin_user
from app.schemas.users import AdminCreate


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

# password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# jwt security
security = HTTPBearer()

# file uploading dir
UPLOAD_DIR = Path("uploads/profiles")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# registration
@router.post("/registration/")
def create_user(
    background_tasks: BackgroundTasks,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    contact_No: str = Form(...),
    password: str = Form(...),
    profile_image: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    userExist=db.query(UserTable).filter(UserTable.email==email).first()
    if userExist is not None:
        raise HTTPException(
            status_code=409,
            detail="User already exists"
        )
        
     # Initially image path None rakho
    # Agar user image upload nahi karega toh ye None rahega
    image_path = None

    # Check karo ki image upload hui hai aur filename available hai
    if profile_image and profile_image.filename:

        # Uploaded file ka reported content type check karo
        # Sirf JPEG, PNG aur WebP allow kar rahe hain
        if profile_image.content_type not in {
            "image/jpeg",
            "image/png",
            "image/webp"
        }:

            # Allowed type nahi hai toh request reject karo
            raise HTTPException(
                status_code=400,
                detail="Only JPEG, PNG and WebP images are allowed"
            )

        # Original filename se extension nikalo
        # Example: photo.JPG se .jpg
        extension = Path(profile_image.filename).suffix.lower()

        # UUID se unique filename generate karo
        # Example: a1b2c3...jpg
        filename = f"{uuid.uuid4().hex}{extension}"

        # Folder path aur filename ko combine karo
        file_path = UPLOAD_DIR / filename

        # Destination file ko binary write mode mein open karo
        with file_path.open("wb") as buffer:

            # Uploaded image ka content destination file mein copy karo
            shutil.copyfileobj(
                profile_image.file,
                buffer
            )

        # Saved image ka path string mein store karo
        # Ye path baad mein database mein save hoga
        image_path = file_path.as_posix()

    # Password ko bcrypt se hash karo
    # Database mein original password save nahi karna
    hashed_password = pwd_context.hash(password)
    
    # email sending
    background_tasks.add_task(
    send_welcome_email,
    email,
    first_name
    )


    # UserTable model ka naya object banao
    new_user = UserTable(
        first_name=first_name,
        last_name=last_name,
        email=email,
        contact_No=contact_No,
        password=hashed_password,
        # Image ka path save karo
        # Image nahi hogi toh value None hogi
        profile_image=image_path
    )

    # Database operations ko safely handle karne ki koshish
    try:

        # Naye user ko database session mein add karo
        db.add(new_user)

        # Database transaction commit karke record save karo
        db.commit()

        # Database se latest values object mein refresh karo
        # Jaise auto-generated user ID
        db.refresh(new_user)

        # Frontend ko successful registration response bhejo
        return {
            "message": "User registered successfully",
            "name": first_name
        }

    # Agar database operation mein exception aata hai
    except Exception:

        # Failed database transaction ko rollback karo
        db.rollback()

        # Agar image save ho chuki hai toh use delete karne ki
        # koshish karo, taaki orphan file na reh jaaye
        if image_path:
            Path(image_path).unlink(missing_ok=True)

        # Client ko generic server error bhejo
        raise HTTPException(
            status_code=500,
            detail="Could not register user"
        )

    # Ye block success ya failure, dono cases mein chalega
    finally:

        # Agar upload file object hai toh use close karo
        if profile_image:
            profile_image.file.close()


@router.post("/login")
def login_user(data:UserLogin,db:Session=Depends(get_db)):
    verify_email=db.query(UserTable).filter(UserTable.email==data.email).first()
    
    if verify_email is not None:
        if pwd_context.verify(data.password,verify_email.password):
            access_token = create_access_token(verify_email.id)
            return{
                "message":"login successful",
                "access_token":access_token,
                'token_type':'bearer'
                
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Wrong Password Please try again"
            )
    raise HTTPException(
        status_code=404,
        detail="User email is not found"
    )
    



@router.post("/admin/create/", status_code=201)
def create_admin(
    data: AdminCreate,
    current_admin: UserTable = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    # Duplicate email check
    existing_email = db.query(UserTable).filter(
        UserTable.email == str(data.email)
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Duplicate contact check
    existing_contact = db.query(UserTable).filter(
        UserTable.contact_No == data.contact_No
    ).first()

    if existing_contact:
        raise HTTPException(
            status_code=409,
            detail="Contact number already registered"
        )

    new_admin = UserTable(
        first_name=data.first_name,
        last_name=data.last_name,
        email=str(data.email),
        contact_No=data.contact_No,
        password=pwd_context.hash(data.password),
        is_admin=True,
        is_active=True
    )

    try:
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        return {
            "message": "Admin created successfully",
            "admin_id": new_admin.id,
            "created_by": current_admin.id
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create admin"
        )

@router.get("/admin/all-users/")
def get_all_users(
    current_admin: UserTable = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    users = db.query(UserTable).all()

    return {
        "total_users": len(users),
        "users": [
            {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "contact_No": user.contact_No,
                "is_admin": user.is_admin,
                "is_active": user.is_active
            }
            for user in users
        ]
    }



