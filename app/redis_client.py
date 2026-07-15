"""
Redis connection helper.

REDIS_HOST / REDIS_PORT are read from the environment so the same image
works unmodified across all three networking experiments:

- bridge network : REDIS_HOST=redis            (Docker DNS resolves the service name)
- host network   : REDIS_HOST=127.0.0.1         (container shares the host's network stack)
- none network   : there is no reachable host; connection will fail on purpose
"""
import os
import socket

import redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _client


def redis_ping() -> dict:
    """Returns connectivity info instead of raising, so /network-info stays useful
    even when the Redis host is unreachable (e.g. in the 'none' network experiment)."""
    info = {
        "redis_host_configured": REDIS_HOST,
        "redis_port_configured": REDIS_PORT,
        "container_hostname": socket.gethostname(),
    }
    try:
        client = get_redis()
        pong = client.ping()
        info["reachable"] = bool(pong)
    except Exception as exc:  # noqa: BLE001 - want to surface any failure reason
        info["reachable"] = False
        info["error"] = str(exc)
    return info
