import pytest
from rest_framework.exceptions import PermissionDenied

from gamification import services as gamification_services
from gamification.models import Badge
from matches import services as match_services
from matches.models import Match
from notifications import services as notification_services
from notifications.models import Notification
from teams import services as team_services
from tournaments import services as tournament_services
from tournaments.models import Tournament, TournamentAdmin, TournamentRegistration

pytestmark = pytest.mark.django_db


def test_notify_creates_a_notification_for_the_recipient(make_player):
    player = make_player("recipient")

    notification = notification_services.notify(
        recipient=player.user, type=Notification.Type.BADGE_EARNED, message="hello", link="/x"
    )

    assert notification.recipient_id == player.user_id
    assert notification.is_read is False


def test_notify_many_creates_one_per_recipient(make_player):
    a = make_player("a")
    b = make_player("b")

    notification_services.notify_many(
        recipients=[a.user, b.user], type=Notification.Type.TOURNAMENT_STARTED, message="go", link="/x"
    )

    assert Notification.objects.filter(recipient=a.user).count() == 1
    assert Notification.objects.filter(recipient=b.user).count() == 1


def test_mark_read_requires_ownership(make_player):
    owner = make_player("owner")
    other = make_player("other")
    notification = notification_services.notify(
        recipient=owner.user, type=Notification.Type.BADGE_EARNED, message="hi"
    )

    with pytest.raises(PermissionDenied):
        notification_services.mark_read(notification=notification, acting_user=other.user)

    notification_services.mark_read(notification=notification, acting_user=owner.user)
    notification.refresh_from_db()
    assert notification.is_read is True


def test_mark_all_read_only_touches_own_unread(make_player):
    owner = make_player("owner2")
    other = make_player("other2")
    notification_services.notify(recipient=owner.user, type=Notification.Type.BADGE_EARNED, message="a")
    notification_services.notify(recipient=owner.user, type=Notification.Type.BADGE_EARNED, message="b")
    other_notification = notification_services.notify(
        recipient=other.user, type=Notification.Type.BADGE_EARNED, message="c"
    )

    notification_services.mark_all_read(acting_user=owner.user)

    assert not Notification.objects.filter(recipient=owner.user, is_read=False).exists()
    other_notification.refresh_from_db()
    assert other_notification.is_read is False


def test_team_invite_notifies_the_invited_player(make_player):
    captain = make_player("invcap")
    invitee = make_player("invitee")
    team = team_services.create_team(creator=captain, name="Invite FC", city="Qarshi")

    team_services.invite_player(team=team, acting_user=captain.user, player_id=invitee.player_id)

    assert Notification.objects.filter(
        recipient=invitee.user, type=Notification.Type.TEAM_INVITE
    ).exists()


def test_badge_award_notifies_the_player(make_player, make_superuser):
    admin = make_superuser()
    player = make_player("badgee")
    badge = Badge.objects.create(name="Top Scorer", icon="🔥")

    gamification_services.award_badge(badge=badge, player=player, acting_user=admin)

    assert Notification.objects.filter(
        recipient=player.user, type=Notification.Type.BADGE_EARNED
    ).exists()


def test_registration_review_notifies_the_captain(make_player, make_superuser):
    admin = make_superuser()
    captain = make_player("regcap")
    team = team_services.create_team(creator=captain, name="Reg FC", city="Qarshi")
    tournament = Tournament.objects.create(
        name="Reg Cup",
        city="Qarshi",
        status=Tournament.Status.REGISTRATION_OPEN,
        created_by=admin,
    )
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    registration = tournament_services.apply_to_tournament(tournament=tournament, team=team, acting_user=captain.user)

    tournament_services.review_registration(registration=registration, acting_user=admin, approve=True)

    assert Notification.objects.filter(
        recipient=captain.user, type=Notification.Type.REGISTRATION_APPROVED
    ).exists()


def _setup_match(make_player, tournament):
    home_captain = make_player("mnhomecap")
    away_captain = make_player("mnawaycap")
    home_team = team_services.create_team(creator=home_captain, name="MN Home", city="Qarshi")
    away_team = team_services.create_team(creator=away_captain, name="MN Away", city="Qarshi")
    home_reg = TournamentRegistration.objects.create(
        tournament=tournament, team=home_team, status=TournamentRegistration.Status.APPROVED
    )
    away_reg = TournamentRegistration.objects.create(
        tournament=tournament, team=away_team, status=TournamentRegistration.Status.APPROVED
    )
    match = Match.objects.create(tournament=tournament, home_registration=home_reg, away_registration=away_reg)
    return match, home_captain, away_captain


def test_finishing_a_match_notifies_both_captains(make_player, make_superuser):
    admin = make_superuser()
    tournament = Tournament.objects.create(
        name="Notify Cup", city="Qarshi", status=Tournament.Status.IN_PROGRESS, created_by=admin
    )
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    match, home_captain, away_captain = _setup_match(make_player, tournament)

    match_services.submit_result(match=match, home_score=2, away_score=1, acting_user=admin)

    assert Notification.objects.filter(recipient=home_captain.user, type=Notification.Type.MATCH_RESULT).exists()
    assert Notification.objects.filter(recipient=away_captain.user, type=Notification.Type.MATCH_RESULT).exists()


def test_disputing_a_match_notifies_tournament_admins(make_player, make_superuser):
    admin = make_superuser()
    tournament = Tournament.objects.create(
        name="Dispute Notify Cup",
        city="Qarshi",
        status=Tournament.Status.IN_PROGRESS,
        created_by=admin,
        require_match_confirmation=True,
    )
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    match, home_captain, away_captain = _setup_match(make_player, tournament)
    match_services.submit_result(match=match, home_score=0, away_score=3, acting_user=admin)

    match_services.dispute_result(match=match, acting_user=home_captain.user)

    assert Notification.objects.filter(recipient=admin, type=Notification.Type.MATCH_DISPUTED).exists()


def test_notification_list_api_is_scoped_to_current_user(api_client, make_player):
    mine = make_player("apime")
    other = make_player("apiother")
    notification_services.notify(recipient=mine.user, type=Notification.Type.BADGE_EARNED, message="mine")
    notification_services.notify(recipient=other.user, type=Notification.Type.BADGE_EARNED, message="not mine")

    api_client.force_authenticate(user=mine.user)
    resp = api_client.get("/api/v1/notifications/")

    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["message"] == "mine"


def test_unread_count_endpoint(api_client, make_player):
    player = make_player("unreadcount")
    notification_services.notify(recipient=player.user, type=Notification.Type.BADGE_EARNED, message="a")
    notification_services.notify(recipient=player.user, type=Notification.Type.BADGE_EARNED, message="b")

    api_client.force_authenticate(user=player.user)
    resp = api_client.get("/api/v1/notifications/unread-count/")

    assert resp.status_code == 200
    assert resp.data["count"] == 2


def test_mark_all_read_endpoint(api_client, make_player):
    player = make_player("markallread")
    notification_services.notify(recipient=player.user, type=Notification.Type.BADGE_EARNED, message="a")
    notification_services.notify(recipient=player.user, type=Notification.Type.BADGE_EARNED, message="b")

    api_client.force_authenticate(user=player.user)
    resp = api_client.post("/api/v1/notifications/mark-all-read/")

    assert resp.status_code == 204
    assert not Notification.objects.filter(recipient=player.user, is_read=False).exists()


def test_cannot_mark_another_users_notification_as_read(api_client, make_player):
    owner = make_player("mrowner")
    other = make_player("mrother")
    notification = notification_services.notify(recipient=owner.user, type=Notification.Type.BADGE_EARNED, message="a")

    api_client.force_authenticate(user=other.user)
    resp = api_client.post(f"/api/v1/notifications/{notification.id}/mark-read/")

    assert resp.status_code == 404
