#  app/schemas/webhook_schema.py

from pydantic import BaseModel
from datetime import datetime

class WebhookBase(BaseModel):
    event: str  # Event type
    data: dict  # Event data
    signature: str  # Signature
    timestamp: str  # Timestamp
    nonce: str  # Nonce

    class Config:
        # Ensure we support dict type for data
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Automatically convert datetime
        }


class WebhookCreate(WebhookBase):
    pass


class WebhookResponse(WebhookBase):
    pass