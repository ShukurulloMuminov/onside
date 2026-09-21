from rest_framework import serializers

from teams.serializers import TeamSerializer

from .models import Group, GroupMembership, Tournament, TournamentRegistration, TournamentStage


class TournamentSerializer(serializers.ModelSerializer):
    team_count = serializers.SerializerMethodField()

    class Meta:
        model = Tournament
        fields = [
            "id",
            "name",
            "slug",
            "banner",
            "description",
            "organizer",
            "city",
            "venue",
            "start_date",
            "end_date",
            "format",
            "status",
            "max_teams",
            "prize_info",
            "points_win",
            "points_draw",
            "points_loss",
            "tie_breaker_config",
            "groups_count",
            "teams_per_group",
            "qualifiers_per_group",
            "require_match_confirmation",
            "team_count",
        ]
        read_only_fields = ["id", "slug", "team_count"]

    def get_team_count(self, obj) -> int:
        return obj.registrations.filter(status=TournamentRegistration.Status.APPROVED).count()


class TournamentRegistrationSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)

    class Meta:
        model = TournamentRegistration
        fields = [
            "id",
            "tournament",
            "team",
            "status",
            "applied_by",
            "reviewed_by",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = [f for f in fields if f != "tournament"]


class ApplyToTournamentSerializer(serializers.Serializer):
    team_slug = serializers.SlugField()


class GroupMembershipSerializer(serializers.ModelSerializer):
    team = TeamSerializer(source="registration.team", read_only=True)

    class Meta:
        model = GroupMembership
        fields = ["id", "team"]
        read_only_fields = fields


class GroupSerializer(serializers.ModelSerializer):
    memberships = GroupMembershipSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ["id", "name", "memberships"]
        read_only_fields = fields


class TournamentStageSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = TournamentStage
        fields = ["id", "type", "name", "order", "groups"]
        read_only_fields = fields


class GenerateGroupsSerializer(serializers.Serializer):
    """Empty body — groups_count/teams_per_group are read from the
    Tournament itself so the config lives in one place."""
