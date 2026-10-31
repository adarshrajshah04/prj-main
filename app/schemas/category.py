from pydantic import BaseModel,Field


# create category
class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    
# Update Category
class CategoryUpdate(BaseModel):
    name: str  = Field( min_length=2, max_length=100)
    description: str  
    is_active: bool  


# Category Response
class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    image: str | None
    is_active: bool

    model_config = {"from_attributes": True}