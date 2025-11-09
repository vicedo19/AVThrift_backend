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
