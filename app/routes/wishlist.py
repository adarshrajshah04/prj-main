from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.model.wishlist import WishlistTable
from app.model.properties import PropertyTable
from app.model.user import UserTable
from app.utils.auth import get_current_user


router = APIRouter(
    prefix="/wishlist",
    tags=["Wishlist"]
)


# ADD TO WISHLIST
@router.post("/{property_id}")
def add_wishlist(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):

    property_data = db.query(PropertyTable).filter(
        PropertyTable.id == property_id
    ).first()

    if not property_data:
        raise HTTPException(
            status_code=404,
            detail="Property not found"
        )

    existing = db.query(WishlistTable).filter(
        WishlistTable.user_id == current_user.id,
        WishlistTable.property_id == property_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Property already exists in wishlist"
        )

    new_wishlist = WishlistTable(
        user_id=current_user.id,
        property_id=property_id
    )

    db.add(new_wishlist)
    db.commit()
    db.refresh(new_wishlist)

    return {
        "message": "Property added to wishlist successfully",
        "wishlist_id": new_wishlist.id,
        "property_id": property_id
    }


# GET USER WISHLIST
@router.get("/")
def get_wishlist(
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):

    wishlist_data = db.query(WishlistTable).options(
        joinedload(WishlistTable.property)
    ).filter(
        WishlistTable.user_id == current_user.id
    ).all()

    data = []

    for item in wishlist_data:

        property_data = item.property

        data.append({
            "wishlist_id": item.id,
            "property_id": property_data.id,
            "category_id": property_data.category_id,
            "category_name": property_data.category.name if property_data.category else None,
            "name": property_data.name,
            "description": property_data.description,
            "location": property_data.location,
            "price_per_night": property_data.price_per_night,
            "guest_capacity": property_data.guest_capacity,
            "is_active": property_data.is_active,
            "cover_image": property_data.cover_image,
            "images": property_data.images or [],
            "created_at": item.created_at
        })

    return {
        "message": "Wishlist fetched successfully",
        "total": len(data),
        "data": data
    }


# REMOVE FROM WISHLIST
@router.delete("/{property_id}")
def remove_wishlist(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):

    wishlist = db.query(WishlistTable).filter(
        WishlistTable.user_id == current_user.id,
        WishlistTable.property_id == property_id
    ).first()

    if not wishlist:
        raise HTTPException(
            status_code=404,
            detail="Property not found in wishlist"
        )

    db.delete(wishlist)
    db.commit()

    return {
        "message": "Property removed from wishlist successfully"
    }


# CHECK WISHLIST
@router.get("/check/{property_id}")
def check_wishlist(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):

    wishlist = db.query(WishlistTable).filter(
        WishlistTable.user_id == current_user.id,
        WishlistTable.property_id == property_id
    ).first()

    return {
        "property_id": property_id,
        "is_wishlisted": wishlist is not None
    }