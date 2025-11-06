"""URL routes for the users app.

Includes authentication endpoints, profile access, and flows for
password reset, email verification, email change, and JWT logout.
"""

from django.urls import path

from .views import (
    current_user,
    email_reset_confirm,
    email_reset_request,
    email_verification_confirm,
    email_verification_request,
    password_reset_confirm,
    password_reset_request,
    register,
)

urlpatterns = [
    path("profile/", current_user, name="profile"),
    path("register/", register, name="register"),
    path("password-reset/", password_reset_request, name="password_reset_request"),
    path("password-reset/confirm/", password_reset_confirm, name="password_reset_confirm"),
    path("email-verify/", email_verification_request, name="email_verification_request"),
    path("email-verify/confirm/", email_verification_confirm, name="email_verification_confirm"),
    path("email-reset/", email_reset_request, name="email_reset_request"),
    path("email-reset/confirm/", email_reset_confirm, name="email_reset_confirm"),
]
