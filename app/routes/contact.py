from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.model.contact import ContactTable
from app.schemas.contact import ContactCreate, ContactResponse
from app.utils.auth import get_admin_user

router = APIRouter(prefix="/contact", tags=["Contact"])


# User submits contact form
@router.post("/", response_model=ContactResponse)
def create_contact(
    data: ContactCreate,
    db: Session = Depends(get_db)
):
    new_contact = ContactTable(
        name=data.name,
        email=data.email,
        subject=data.subject,
        message=data.message
    )

    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    return new_contact


# Admin gets all contact messages
@router.get("/all", response_model=list[ContactResponse])
def get_all_contacts(
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    return db.query(ContactTable).order_by(
        ContactTable.created_at.desc()
    ).all()


# Admin gets one contact message
@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    contact = db.query(ContactTable).filter(
        ContactTable.id == contact_id
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contact


# Admin marks message as read
@router.patch("/{contact_id}/read")
def mark_contact_read(
    contact_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    contact = db.query(ContactTable).filter(
        ContactTable.id == contact_id
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact.is_read = True
    db.commit()

    return {"message": "Contact marked as read"}


# Admin deletes contact message
@router.delete("/{contact_id}")
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    contact = db.query(ContactTable).filter(
        ContactTable.id == contact_id
    ).first()

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()

    return {"message": "Contact deleted successfully"}