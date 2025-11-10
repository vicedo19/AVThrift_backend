from decouple import config as _config

from .base import *  # noqa

DEBUG = True

# In dev, allow the browsable API and relaxed CORS
CORS_ALLOW_ALL_ORIGINS = True

# Email backend for dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Optional Redis cache for local parity

_REDIS_URL = _config("REDIS_URL", default="")
if _REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _REDIS_URL,
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
