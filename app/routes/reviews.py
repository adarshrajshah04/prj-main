from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.model.review import ReviewTable
from app.model.properties import PropertyTable
from app.schemas.review import (
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse
)
from app.model.user import UserTable
from app.utils.auth import get_current_user


router = APIRouter(prefix="/reviews", tags=["Reviews"])


# CREATE REVIEW
@router.post("/", response_model=ReviewResponse)
def create_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):

    property_data = db.query(PropertyTable).filter(
        PropertyTable.id == review.property_id
    ).first()

    if not property_data:
        raise HTTPException(
            status_code=404,
            detail="Property not found"
        )

    existing_review = db.query(ReviewTable).filter(
        ReviewTable.user_id == current_user.id,
        ReviewTable.property_id == review.property_id
    ).first()

    if existing_review:
        raise HTTPException(
            status_code=400,
            detail="You have already reviewed this property"
        )

    new_review = ReviewTable(
        user_id=current_user.id,
        property_id=review.property_id,
        rating=review.rating,
        comment=review.comment
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return new_review


# GET ALL REVIEWS
@router.get("/")
def all_reviews(db: Session = Depends(get_db)):

    reviews = db.query(ReviewTable).options(
        joinedload(ReviewTable.user),
        joinedload(ReviewTable.property)
    ).all()

    data = []

    for review in reviews:
        data.append({
            "id": review.id,
            "user_id": review.user_id,
            "user_name": review.user.first_name,
            "user_profile_picture": review.user.profile_image,
            "property_id": review.property_id,
            "property_name": review.property.name,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at
        })

    return {
        "message": "All reviews",
        "data": data
    }


# GET PROPERTY REVIEWS
@router.get("/property/{property_id}")
def property_reviews(
    property_id: int,
    db: Session = Depends(get_db)
):

    reviews = db.query(ReviewTable).filter(
        ReviewTable.property_id == property_id
    ).options(
        joinedload(ReviewTable.user)
    ).all()

    data = []

    for review in reviews:
        data.append({
        "id": review.id,
        "user_id": review.user_id,
        "user_name": review.user.first_name,
        "user_profile_picture": review.user.profile_image,
        "property_id": review.property_id,
        "property_name": review.property.name,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at
        })

    return {
        "message": "Property reviews",
        "data": data
    }


# GET SINGLE REVIEW
@router.get("/{review_id}")
def single_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    review = db.query(ReviewTable).filter(
        ReviewTable.id == review_id
    ).first()

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return {
        "id": review.id,
        "user_id": review.user_id,
        "user_name": review.user.first_name,
        "user_profile_picture": review.user.profile_image,
        "property_id": review.property_id,
        "property_name": review.property.name,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at
    }




# UPDATE REVIEW
@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):

    existing_review = db.query(ReviewTable).filter(
        ReviewTable.id == review_id
    ).first()

    if not existing_review:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    if existing_review.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot update another user's review"
        )

    update_data = review.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(existing_review, key, value)

    db.commit()
    db.refresh(existing_review)

    return existing_review


# DELETE REVIEW
@router.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: UserTable = Depends(get_current_user)
):

    review = db.query(ReviewTable).filter(
        ReviewTable.id == review_id
    ).first()

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You cannot delete another user's review"
        )

    db.delete(review)
    db.commit()

    return {
        "message": "Review deleted successfully"
    }