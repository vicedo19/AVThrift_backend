"""Shared enumerations and choices used across apps."""

from django.db import models


class ActiveInactive(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class DraftPublished(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"


class MovementType(models.TextChoices):
    INBOUND = "in", "Inbound"
    OUTBOUND = "out", "Outbound"
    ADJUST = "adjust", "Adjust"


class ReservationState(models.TextChoices):
    ACTIVE = "active", "Active"
    RELEASED = "released", "Released"
    CONVERTED = "converted", "Converted"


class CartStatus(models.TextChoices):
    """Statuses for shopping carts."""

    ACTIVE = "active", "Active"
    ORDERED = "ordered", "Ordered"
    ABANDONED = "abandoned", "Abandoned"


class OrderStatus(models.TextChoices):
    """Lifecycle statuses for orders."""

    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    CANCELLED = "cancelled", "Cancelled"


class PaymentIntentStatus(models.TextChoices):
    """Statuses for payment intents across providers."""

    INITIALIZED = "initialized", "Initialized"
    PROCESSING = "processing", "Processing"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class PaymentProvider(models.TextChoices):
    """Supported payment providers."""

    PAYSTACK = "paystack", "Paystack"


class Currency(models.TextChoices):
    """Supported currency choices."""

    NGN = "NGN", "Nigerian Naira"
    USD = "USD", "US Dollar"
    GHS = "GHS", "Ghanaian Cedi"
    ZAR = "ZAR", "South African Rand"
    KES = "KES", "Kenyan Shilling"
    XOF = "XOF", "West African CFA Franc"
