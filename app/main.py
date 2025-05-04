import ast
from hashlib import sha256
import hmac
import json
from typing import List
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine
from app.cache import get_subscription_from_cache, set_subscription_in_cache
from . import models, schemas, database
from .tasks import deliver_webhook_task
from sqlalchemy.orm import sessionmaker

app = FastAPI()

@app.on_event("startup")
async def check_db():
    try:
        async with database.engine.connect() as conn:
            print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")



@app.post("/subscriptions/", response_model=schemas.Subscription)
async def create_subscription(
    sub: schemas.SubscriptionCreate,
    db: AsyncSession = Depends(database.get_db)
):
    db_sub = models.Subscription(**sub.dict())
    db.add(db_sub)
    await db.commit()
    return db_sub

@app.get("/subscriptions/{sub_id}", response_model=schemas.Subscription)
async def get_subscription(
    sub_id: int,
    db: AsyncSession = Depends(database.get_db)
):
    sub = await db.get(models.Subscription, sub_id)
    if not sub:
        raise HTTPException(404, "Subscription not found")
    return sub

@app.post("/ingest/{sub_id}", status_code=202)
async def ingest_webhook(
    sub_id: int,
    payload: dict,
    x_hub_signature: str = Header(None),
    db: AsyncSession = Depends(database.get_db)
):
    sub_data = get_subscription_from_cache(sub_id)
    if sub_data:
        sub_dict = ast.literal_eval(sub_data) 
    else:
        sub = await db.get(models.Subscription, sub_id)
        if not sub:
            raise HTTPException(404, "Subscription not found")
        sub_dict = {
            "id": sub.id,
            "target_url": sub.target_url,
            "secret": sub.secret,
        }
        set_subscription_in_cache(sub_id, sub_dict)

    if sub_dict["secret"]:
        sig = hmac.new(sub_dict["secret"].encode(), json.dumps(payload).encode(), sha256).hexdigest()
        if f"sha256={sig}" != x_hub_signature:
            raise HTTPException(403, "Invalid signature")
    delivery = models.WebhookDelivery(
        subscription_id=sub_id,
        payload=payload,
        status="queued"
    )
    db.add(delivery)
    await db.commit()
    deliver_webhook_task.delay(sub_id, payload, delivery.id)
    return {"status": "queued"}

@app.get("/deliveries/{delivery_id}", response_model=schemas.DeliveryStatus)
async def get_delivery_status(
    delivery_id: int,
    db: AsyncSession = Depends(database.get_db)
):
    delivery = await db.get(models.WebhookDelivery, delivery_id)
    if not delivery:
        raise HTTPException(404, "Delivery not found")
    return delivery

@app.get("/deliveries/", response_model=List[schemas.DeliveryStatus])
async def list_deliveries(db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(models.WebhookDelivery))
    return result.scalars().all()