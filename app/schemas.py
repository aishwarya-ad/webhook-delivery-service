from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class SubscriptionCreate(BaseModel):
    target_url: str
    secret: Optional[str] = None

class Subscription(BaseModel):
    id: int
    target_url: str
    secret: Optional[str] = None
    class Config:
        from_attributes = True

class DeliveryStatus(BaseModel):
    id: int
    subscription_id: int
    payload: Dict[str, Any]  
    status: str
    attempts: int
    created_at: datetime 
    class Config:
        from_attributes = True