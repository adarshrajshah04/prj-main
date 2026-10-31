from pydantic import BaseModel, ConfigDict
from datetime import datetime


class NotificationResponse(BaseModel):
    id: int
    user_id: int | None
    username: str
    action: str
    entity: str
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)