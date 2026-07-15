import json
import socket

from fastapi import FastAPI
from pydantic import BaseModel

from app.database import add_item, init_db, list_items
from app.redis_client import get_redis, redis_ping

app = FastAPI(title="FastAPI + SQLite + Redis Lab")


class ItemIn(BaseModel):
    name: str


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def root():
    return {
        "app": "fastapi-sqlite-redis",
        "hostname": socket.gethostname(),
        "endpoints": [
            "GET  /health",
            "GET  /network-info",
            "GET  /items",
            "POST /items",
            "GET  /items/cached",
            "GET  /counter",
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/network-info")
def network_info():
    """Shows how this container currently sees the network - useful while
    switching between bridge / host / none Docker network modes."""
    try:
        host_ip = socket.gethostbyname(socket.gethostname())
    except Exception:  # noqa: BLE001
        host_ip = "unresolvable"

    return {
        "container_hostname": socket.gethostname(),
        "container_ip": host_ip,
        "redis": redis_ping(),
    }


@app.post("/items")
def create_item(item: ItemIn):
    created = add_item(item.name)
    # Any write invalidates the cached list so /items/cached stays correct.
    get_redis().delete("items:cache")
    return created


@app.get("/items")
def get_items():
    return list_items()


@app.get("/items/cached")
def get_items_cached():
    """Cache-aside pattern: try Redis first, fall back to SQLite, then populate cache."""
    r = get_redis()
    cached = None
    try:
        cached = r.get("items:cache")
    except Exception:  # noqa: BLE001
        pass  # Redis unreachable (e.g. 'none' network mode) - fall through to SQLite

    if cached:
        return {"source": "redis-cache", "items": json.loads(cached)}

    items = list_items()
    try:
        r.set("items:cache", json.dumps(items), ex=30)
    except Exception:  # noqa: BLE001
        pass
    return {"source": "sqlite", "items": items}


@app.get("/counter")
def counter():
    """Simple INCR counter to demonstrate a live Redis round trip per request."""
    r = get_redis()
    try:
        value = r.incr("hit_counter")
        return {"source": "redis", "hit_counter": value}
    except Exception as exc:  # noqa: BLE001
        return {"source": "redis-unreachable", "error": str(exc)}
