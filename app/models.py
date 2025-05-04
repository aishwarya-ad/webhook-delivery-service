from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from .database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    target_url = Column(String, nullable=False)
    secret = Column(String) 

class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, default="pending")
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # http_status = Column(Integer) 
    # error = Column(String)