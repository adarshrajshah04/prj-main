from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.model.notification import NotificationTable
from app.schemas.notification import NotificationResponse
from app.utils.auth import get_admin_user

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.get("/", response_model=list[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    notifications = (
        db.query(NotificationTable)
        .order_by(NotificationTable.created_at.desc())
        .all()
    )

    return notifications