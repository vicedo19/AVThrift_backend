"""User models for authentication and account management.

This module defines the custom `User` model which extends Django's
`AbstractUser` to enable email uniqueness, verification state, and
pending email changes for secure email updates.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with unique email and verification state.

    Fields:
    - email: the primary email, unique at the database level (normalized).
    - email_verified: whether the primary email has been verified.
    - pending_email: a temporary email awaiting verification and confirmation.
    """

    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    pending_email = models.EmailField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """Normalize email fields and persist.

        Ensures both `email` and `pending_email` are stored in lowercase
        without surrounding whitespace so uniqueness checks are reliable.
        """
        if self.email:
            self.email = self.email.strip().lower()
        if self.pending_email:
            self.pending_email = self.pending_email.strip().lower()
        super().save(*args, **kwargs)
