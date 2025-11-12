from decouple import config as _config

from .base import REST_FRAMEWORK as BASE_REST_FRAMEWORK
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

# DRF throttling scopes for cart endpoints in development
# Define REST_FRAMEWORK explicitly to satisfy flake8 F405 with star imports
REST_FRAMEWORK = {**BASE_REST_FRAMEWORK}
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [
    "rest_framework.throttling.ScopedRateThrottle",
]
_rates = {**BASE_REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})}
_rates.update(
    {
        "cart": "20/min",
        "cart_write": "20/min",
    }
)
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = _rates
