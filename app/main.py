from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import redis
import time
import os

app = FastAPI()

RATE_LIMIT_ENDPOINT =  os.getenv("RATE_LIMIT_ENDPOINT", "/api/test")
MAX_REQUESTS_PER_SECOND = int(os.getenv("MAX_REQUESTS_PER_SECOND", "5"))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def is_rate_limited(ip: str) -> bool:
    """
    Uses a sliding window counter per IP address.
    Key format: rate_limit:<ip>:<current_second>
    Each key expires after 2 seconds (auto-cleanup).
    """
    current_second = int(time.time())
    key = f"rate_limit:{ip}:{current_second}"

    # Increment the request count for this IP in the current second
    count = r.incr(key)

    # Set expiry so Redis auto-cleans old keys
    r.expire(key, 2)

    return count > MAX_REQUESTS_PER_SECOND

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Intercepts every request.
    Only rate limits the configured endpoint.
    """
    if request.url.path == RATE_LIMIT_ENDPOINT:
        client_ip = request.client.host

        if is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Max {MAX_REQUESTS_PER_SECOND} requests/second allowed.",
                    "ip": client_ip
                }
            )
        
    response = await call_next(request)
    return response

@app.get("/api/test")
async def test_endpoint(request: Request):
    return JSONResponse(
        status_code=200,
        content={
            "status": "OK",
            "message": "Request accepted!",
            "ip": request.client.host
        }
    )


@app.get("/health")
async def health_check():
    """Simple health check — Kubernetes uses this."""
    try:
        r.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "redis": "disconnected"}
        )

@app.get("/config")
async def get_config():
    return JSONResponse(
        status_code=200,
        content={
            "rate_limited_endpoint": RATE_LIMIT_ENDPOINT,
            "max_requests_per_second": MAX_REQUESTS_PER_SECOND,
            "redis_host": REDIS_HOST,
            "redis_port": REDIS_PORT
        }
    )
