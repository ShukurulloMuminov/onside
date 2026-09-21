import re

from django.conf import settings
from django.db import transaction
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework.exceptions import ValidationError

from .models import User


def _unique_username(base: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]", "", base).lower() or "player"
    username = base
    n = 1
    while User.objects.filter(username=username).exists():
        n += 1
        username = f"{base}{n}"
    return username


@transaction.atomic
def authenticate_google_id_token(raw_id_token: str) -> User:
    """Verifies a Google Identity Services ID token and returns the
    matching User, creating one (plus an empty PlayerProfile, mirroring
    RegisterSerializer) on first sign-in. Matches on verified email so a
    user who already registered with a password can also sign in with
    Google under the same account.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise ValidationError({"id_token": "Google sign-in is not configured on this server."})

    try:
        idinfo = google_id_token.verify_oauth2_token(
            raw_id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError as exc:
        raise ValidationError({"id_token": "Invalid Google token."}) from exc

    if not idinfo.get("email_verified"):
        raise ValidationError({"id_token": "Google account email is not verified."})

    email = idinfo["email"].lower()

    user = User.objects.filter(email__iexact=email).first()
    if user:
        return user

    from players.models import PlayerProfile

    user = User.objects.create(
        username=_unique_username(email.split("@")[0]),
        email=email,
        first_name=idinfo.get("given_name", "")[:150],
        last_name=idinfo.get("family_name", "")[:150],
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])
    PlayerProfile.objects.create(user=user)
    return user
