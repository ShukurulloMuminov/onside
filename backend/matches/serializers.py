from rest_framework import serializers

from players.serializers import PlayerProfileSerializer

from .models import Match, MatchEvent


class _RegistrationTeamSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="team.id")
    name = serializers.CharField(source="team.name")
    slug = serializers.CharField(source="team.slug")
    logo = serializers.ImageField(source="team.logo", allow_null=True)


class MatchEventSerializer(serializers.ModelSerializer):
    player = PlayerProfileSerializer(read_only=True)

    class Meta:
        model = MatchEvent
        fields = [
            "id",
            "match",
            "type",
            "player",
            "team_registration",
            "minute",
            "related_event",
            "created_at",
        ]
        read_only_fields = ["id", "match", "player", "created_at"]


class MatchEventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchEvent
        fields = ["type", "player", "team_registration", "minute", "related_event"]


class MatchSerializer(serializers.ModelSerializer):
    home_team = serializers.SerializerMethodField()
    away_team = serializers.SerializerMethodField()
    tournament_slug = serializers.SlugRelatedField(
        source="tournament", slug_field="slug", read_only=True
    )
    tournament_name = serializers.CharField(source="tournament.name", read_only=True)
    events = MatchEventSerializer(many=True, read_only=True)
    confirmed_registrations = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = [
            "id",
            "tournament",
            "tournament_slug",
            "tournament_name",
            "stage",
            "group",
            "knockout_round",
            "home_registration",
            "away_registration",
            "home_team",
            "away_team",
            "scheduled_date",
            "scheduled_time",
            "venue",
            "referee",
            "status",
            "home_score",
            "away_score",
            "penalty_home_score",
            "penalty_away_score",
            "feeds_into_match",
            "feeds_into_slot",
            "events",
            "confirmed_registrations",
        ]
        # Scores are never writable through the generic PATCH — they only
        # change via the submit-result / confirm / force-finalize actions
        # below, which go through matches.services so the confirmation
        # workflow (and the KnockoutService signal it triggers) can never
        # be bypassed by a raw field edit. `status` stays PATCH-able (an
        # admin can still mark a match live/postponed/cancelled) except
        # for the finished transition, blocked in validate_status below.
        read_only_fields = [
            "id",
            "stage",
            "group",
            "knockout_round",
            "home_team",
            "away_team",
            "tournament_slug",
            "tournament_name",
            "feeds_into_match",
            "feeds_into_slot",
            "events",
            "home_score",
            "away_score",
            "penalty_home_score",
            "penalty_away_score",
            "confirmed_registrations",
        ]

    def get_home_team(self, obj) -> dict | None:
        if not obj.home_registration:
            return None
        return _RegistrationTeamSerializer(obj.home_registration).data

    def get_away_team(self, obj) -> dict | None:
        if not obj.away_registration:
            return None
        return _RegistrationTeamSerializer(obj.away_registration).data

    def get_confirmed_registrations(self, obj) -> list[int]:
        return list(obj.confirmations.values_list("team_registration_id", flat=True))

    def validate_status(self, value):
        if value == Match.Status.FINISHED:
            raise serializers.ValidationError(
                "Use submit-result (and confirm/force-finalize) to finish a match, not a direct status edit."
            )
        return value


class MatchResultSubmitSerializer(serializers.Serializer):
    home_score = serializers.IntegerField(min_value=0)
    away_score = serializers.IntegerField(min_value=0)
    penalty_home_score = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    penalty_away_score = serializers.IntegerField(min_value=0, required=False, allow_null=True)
