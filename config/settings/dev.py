from .base import *  # noqa

DEBUG = True

# In dev, allow the browsable API and relaxed CORS
CORS_ALLOW_ALL_ORIGINS = True

# Email backend for dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
