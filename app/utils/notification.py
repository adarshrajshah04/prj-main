from app.database import sessionLocal
from app.model.notification import NotificationTable


def create_notification(
    current_user,
    action: str,
    entity: str,
    description: str
):
    db = sessionLocal()

    try:
        notification = NotificationTable(
            user_id=current_user.id,
            username=current_user.first_name,
            action=action,
            entity=entity,
            description=description
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()