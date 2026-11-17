## redis cache for examinations, examination schedules (slots) and rubrics
## if redis is not running the app still works, it just does not cache
import json
import time
import redis
from redis.retry import Retry
from redis.backoff import NoBackoff

## retry=0: if redis is not running, give up at once instead of retrying (windows is slow to refuse connections)
r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True,
                socket_connect_timeout=1, socket_timeout=1, retry=Retry(NoBackoff(), 0))
EXPIRY = 300  ## seconds (5 minutes)
redis_down_until = 0  ## if redis is not running, do not try again for 60 seconds


def redis_failed():
    global redis_down_until
    redis_down_until = time.time() + 60


def redis_available():
    if time.time() < redis_down_until:
        return False
    try:
        r.ping()
        return True
    except redis.RedisError:
        redis_failed()
        return False


def cache_get(key):
    if time.time() < redis_down_until:
        return None
    try:
        value = r.get("emp:" + key)
    except redis.RedisError:
        redis_failed()
        return None
    if value is None:
        return None
    return json.loads(value)


def cache_set(key, value, expiry=EXPIRY):
    if time.time() < redis_down_until:
        return
    try:
        r.setex("emp:" + key, expiry, json.dumps(value))
    except redis.RedisError:
        redis_failed()


def cache_clear():
    ## called after anything about examinations / slots / bookings / rubrics changes
    if time.time() < redis_down_until:
        return
    try:
        for key in r.scan_iter("emp:*"):
            r.delete(key)
    except redis.RedisError:
        redis_failed()
