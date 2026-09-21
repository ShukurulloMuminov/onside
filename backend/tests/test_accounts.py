from unittest.mock import patch

import pytest
from rest_framework.exceptions import ValidationError

from accounts.models import User
from accounts.services import authenticate_google_id_token
from players.models import PlayerProfile

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def google_client_id(settings):
    settings.GOOGLE_CLIENT_ID = "test-client-id"


def _payload(**overrides):
    payload = {
        "email": "new.player@gmail.com",
        "email_verified": True,
        "given_name": "New",
        "family_name": "Player",
    }
    payload.update(overrides)
    return payload


@patch("accounts.services.google_id_token.verify_oauth2_token")
def test_creates_new_user_and_player_profile(mock_verify):
    mock_verify.return_value = _payload()

    user = authenticate_google_id_token("fake-token")

    assert user.email == "new.player@gmail.com"
    assert user.first_name == "New"
    assert not user.has_usable_password()
    assert PlayerProfile.objects.filter(user=user).exists()


@patch("accounts.services.google_id_token.verify_oauth2_token")
def test_signs_into_existing_account_by_email(mock_verify):
    existing = User.objects.create_user(username="existing", email="existing@gmail.com", password="pw")
    mock_verify.return_value = _payload(email="Existing@gmail.com")

    user = authenticate_google_id_token("fake-token")

    assert user.id == existing.id
    assert User.objects.filter(email__iexact="existing@gmail.com").count() == 1


@patch("accounts.services.google_id_token.verify_oauth2_token")
def test_rejects_unverified_email(mock_verify):
    mock_verify.return_value = _payload(email_verified=False)

    with pytest.raises(ValidationError):
        authenticate_google_id_token("fake-token")


@patch("accounts.services.google_id_token.verify_oauth2_token")
def test_rejects_invalid_token(mock_verify):
    mock_verify.side_effect = ValueError("bad token")

    with pytest.raises(ValidationError):
        authenticate_google_id_token("fake-token")


def test_rejects_when_not_configured(settings):
    settings.GOOGLE_CLIENT_ID = ""
    with pytest.raises(ValidationError):
        authenticate_google_id_token("fake-token")


@patch("accounts.services.google_id_token.verify_oauth2_token")
def test_duplicate_username_gets_suffixed(mock_verify):
    User.objects.create_user(username="taken", email="someone-else@gmail.com", password="pw")
    mock_verify.return_value = _payload(email="taken@gmail.com")

    user = authenticate_google_id_token("fake-token")

    assert user.username != "taken"
    assert user.username.startswith("taken")


def test_multiple_users_can_have_a_blank_phone():
    # phone is unique but optional. A blank form submission produces "",
    # and a CharField unique constraint treats every "" as a duplicate of
    # every other "" — User.save() normalizes "" to NULL to avoid that.
    User.objects.create_user(username="nophone1", password="pw", phone="")
    User.objects.create_user(username="nophone2", password="pw", phone="")

    assert User.objects.filter(username__in=["nophone1", "nophone2"], phone__isnull=True).count() == 2


def test_real_duplicate_phone_numbers_still_conflict():
    from django.db import IntegrityError

    User.objects.create_user(username="hasphone1", password="pw", phone="+998901234567")
    with pytest.raises(IntegrityError):
        User.objects.create_user(username="hasphone2", password="pw", phone="+998901234567")
