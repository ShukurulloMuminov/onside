import pytest
from rest_framework.test import APIClient

from accounts.models import User
from players.models import PlayerProfile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def make_player(db):
    counter = {"n": 0}

    def _make(username=None, city="Qarshi", position=PlayerProfile.Position.MIDFIELDER, **kwargs):
        counter["n"] += 1
        username = username or f"player{counter['n']}"
        user = User.objects.create_user(
            username=username, password="TestPass123!", email=f"{username}@onside.uz", **kwargs
        )
        return PlayerProfile.objects.create(user=user, city=city, position=position)

    return _make


@pytest.fixture
def make_superuser(db):
    def _make(username="superadmin"):
        return User.objects.create_superuser(
            username=username, password="TestPass123!", email=f"{username}@onside.uz"
        )

    return _make
