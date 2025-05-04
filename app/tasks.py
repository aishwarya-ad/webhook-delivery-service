from datetime import datetime, timedelta
from celery import Celery
from sqlalchemy import select

from app.database import SyncSessionLocal
from app.models import Subscription, WebhookDelivery
import httpx

celery = Celery(
    'tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/1'
)

# celery = Celery(
#     'tasks',
#     broker='redis://localhost:6379/0',
#     backend='redis://localhost:6379/1'
# )

@celery.task(bind=True, max_retries=5)
def deliver_webhook_task(self, sub_id: int, payload: dict, delivery_id: int):
    print(f"🛠️ Executing task for delivery_id={delivery_id}")
    with SyncSessionLocal() as db:
        try:
            sub = db.query(Subscription).get(sub_id)
            delivery = db.query(WebhookDelivery).get(delivery_id)
            
            if not sub or not delivery:
                raise ValueError(f"Subscription or WebhookDelivery with given IDs not found")
            
            delivery.status = "processing"
            db.commit()

            with httpx.Client() as client:
                response = client.post(
                    sub.target_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()

            delivery.status = "delivered"
            db.commit()

        except Exception as e:
            delivery.status = "failed"
            delivery.attempts = self.request.retries + 1
            
            if delivery.attempts >= 5:
                delivery.status = "permanently_failed"
            db.commit() 
            print(f"Error occurred: {e}")
            raise self.retry(exc=e, countdown=10 * delivery.attempts)
        else:
            db.commit()
            print(f"Webhook delivery successfully completed for delivery_id={delivery_id}")


@celery.task
def cleanup_old_deliveries():
    with SyncSessionLocal() as db:
        db.query(WebhookDelivery)\
          .filter(WebhookDelivery.created_at < datetime.now() - timedelta(hours=72))\
          .delete()
        db.commit()


celery.conf.beat_schedule = {
    'cleanup-deliveries': {
        'task': 'app.tasks.cleanup_old_deliveries',
        'schedule': timedelta(days=1),
    },
}
