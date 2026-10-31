import threading
import time
from datetime import datetime, timedelta

from app.database import sessionLocal
from app.model.notification import NotificationTable


def delete_old_notifications():
    db = sessionLocal()

    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        db.query(NotificationTable).filter(
            NotificationTable.created_at < cutoff_time
        ).delete(synchronize_session=False)

        db.commit()

    except Exception as e:
        db.rollback()
        print("Notification cleanup error:", e)

    finally:
        db.close()


def start_notification_cleanup():

    def cleanup_loop():
        while True:
            delete_old_notifications()
            time.sleep(60)

    thread = threading.Thread(
        target=cleanup_loop,
        daemon=True
    )

    thread.start()