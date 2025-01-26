#  app/schemas/webhook_interface.py

from pydantic import BaseModel

class WebhookInterface(BaseModel):
    event: str  # Event type
    data: dict  # Event data
    signature: str  # Signature
    timestamp: str  # Timestamp     
    nonce: str  # Nonce 
