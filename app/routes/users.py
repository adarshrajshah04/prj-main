from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form,status,UploadFile
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
from app.utils.jwt import create_access_token,create_refresh_token,verify_refresh_token
from fastapi.security import HTTPBearer
from app.utils.auth import get_admin_user, get_current_user
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

# user login
@router.post("/login")
def login_user(data:UserLogin,db:Session=Depends(get_db)):
    verify_email=db.query(UserTable).filter(UserTable.email==data.email).first()
    
    if verify_email is not None:
        if pwd_context.verify(data.password,verify_email.password):
            access_token = create_access_token(verify_email.id)
            refresh_token = create_refresh_token(verify_email.id)
            return{
                "message":"login successful",
                "access_token":access_token,
                "refresh_token": refresh_token,
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
    

# admin login page
@router.post("/login/admin")
def login_admin(data:UserLogin,db:Session=Depends(get_db)):
    
    verify_email=db.query(UserTable).filter(UserTable.email==data.email).first()
    
    if verify_email is not None:
        if pwd_context.verify(data.password,verify_email.password):
            if verify_email.is_admin == True:
                access_token = create_access_token(verify_email.id)
                refresh_token = create_refresh_token(verify_email.id)
                return{
                        "message":"login successful",
                        "access_token":access_token,
                        "refresh_token": refresh_token,
                        'token_type':'bearer'
                                
                    }
            else:
                raise HTTPException(
                    status_code=403,
                    detail="this is only for admins only"
                )
            
        else:
            raise HTTPException(
                status_code=404,
                detail="Wrong Password Please try again"
            )
    raise HTTPException(
        status_code=404,
        detail="User email is not found"
    )

# create a new admin only admin can create a admin

@router.post("/admin/create/", status_code=201)
def create_admin(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    contact_No: str = Form(...),
    password: str = Form(...),

    profile_image: UploadFile = File(...),

    current_admin: UserTable = Depends(get_admin_user),
    db: Session = Depends(get_db)
):

    existing_email = db.query(UserTable).filter(
        UserTable.email == email
    ).first()

    if existing_email:
        raise HTTPException(409, "Email already registered")

    existing_contact = db.query(UserTable).filter(
        UserTable.contact_No == contact_No
    ).first()

    if existing_contact:
        raise HTTPException(409, "Contact number already registered")

    # Image validation
    allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]

    extension = Path(profile_image.filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(400, "Invalid image format")

    # Save image
    upload_dir = Path("media/admin_profiles")
    upload_dir.mkdir(parents=True, exist_ok=True)

    image_name = f"{uuid.uuid4()}{extension}"
    image_path = upload_dir / image_name

    try:
        with image_path.open("wb") as buffer:
            shutil.copyfileobj(profile_image.file, buffer)

        new_admin = UserTable(
            first_name=first_name,
            last_name=last_name,
            email=email,
            contact_No=contact_No,
            password=pwd_context.hash(password),
            profile_image=f"admin_profiles/{image_name}",
            is_admin=True,
            is_active=True
        )

        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        return {
            "message": "Admin created successfully",
            "admin_id": new_admin.id,
            "profile_image": new_admin.profile_image,
            "created_by": current_admin.id
        }

    except Exception:
        db.rollback()

        if image_path.exists():
            image_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Could not create admin"
        )

    finally:
        profile_image.file.close()
# all user list Admin view only
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
                "is_active": user.is_active,
                "profile_image":user.profile_image
            }
            for user in users
        ]
    }





@router.post("/refresh-token/")
def refresh_access_token(data: RefreshTokenRequest):

    user_id = verify_refresh_token(data.refresh_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    new_access_token = create_access_token(int(user_id))

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
    
    
    
    
# Get logged-in user profile
@router.get("/profile/")
def get_user_profile(
    current_user: UserTable = Depends(get_current_user)
):

    return {
        "message": "User profile fetched successfully",
        "data": {
            "id": current_user.id,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "email": current_user.email,
            "contact_No": current_user.contact_No,
            "profile_image": current_user.profile_image,
            "is_admin": current_user.is_admin,
            "is_active": current_user.is_active
        }
    }