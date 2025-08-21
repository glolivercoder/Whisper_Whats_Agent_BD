# models/webhook_models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class MessageData(BaseModel):
    type: Optional[str] = None
    mediaUrl: Optional[str] = None
    url: Optional[str] = None

class WebhookData(BaseModel):
    event: str
    data: Dict[str, Any]
