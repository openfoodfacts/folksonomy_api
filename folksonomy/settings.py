import os
from typing import Optional

# --- Database Configuration ---
POSTGRES_USER = os.environ.get("POSTGRES_USER", None)
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", None)
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_DATABASE = os.environ.get("POSTGRES_DATABASE", "folksonomy")

# --- Redis Cache Configuration ---
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)  # For production security
CACHE_TTL = int(os.environ.get("CACHE_TTL", 300))  # 5 minutes default

# Cache invalidation patterns (regex supported)
CACHE_INVALIDATION_PATTERNS = [
    "tags:*",
    "product:*",
    "query:*"
]

# --- Authentication ---
FOLKSONOMY_PREFIX = os.environ.get("FOLKSONOMY_PREFIX", "api.folksonomy")
AUTH_PREFIX = os.environ.get("AUTH_PREFIX", "world")
FAILED_AUTH_WAIT_TIME = 2  # Anti-brute force delay

# --- Cache Error Handling ---
CACHE_FAILURE_GRACE_PERIOD = int(os.environ.get("CACHE_FAILURE_GRACE_PERIOD", 30))  # Seconds to wait after cache failure
ENABLE_CACHE = os.environ.get("ENABLE_CACHE", "true").lower() == "true"  # Kill switch

# --- Local Overrides ---
try:
    from local_settings import *  # type: ignore
except ImportError:
    pass

# --- Validation ---
def validate_settings():
    """Validate critical settings at startup"""
    if not POSTGRES_HOST:
        raise ValueError("POSTGRES_HOST must be configured")
    
    if ENABLE_CACHE and not REDIS_HOST:
        raise ValueError("Redis cache enabled but REDIS_HOST not set")

# Call validation on import
validate_settings()
