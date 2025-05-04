from redis import Redis
from datetime import timedelta

redis = Redis(host="localhost", port=6379, decode_responses=True)

def get_subscription_from_cache(sub_id: int):
    return redis.get(f"sub_{sub_id}")

def set_subscription_in_cache(sub_id: int, data: dict, ttl: int = 3600):
    redis.setex(f"sub_{sub_id}", timedelta(seconds=ttl), str(data))