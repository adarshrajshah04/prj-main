from pydantic import BaseModel,EmailStr,Field,ConfigDict

class UserCreate(BaseModel):
    
    first_name:str=Field(min_length=3,max_length=50)
    last_name:str=Field(min_length=1,max_length=50)
    email:EmailStr
    contact_No:int=Field(min_length=10,max_length=15)
    
    password:str=Field(min_length=8, max_length=128)
    

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    contact_No: str
    profile_image: str | None = None
    is_admin: bool
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email:EmailStr
    password:str=Field(min_length=8, max_length=128)

class AdminCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    contact_No: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8, max_length=72)
    
    
class RefreshTokenRequest(BaseModel):
    refresh_token: str