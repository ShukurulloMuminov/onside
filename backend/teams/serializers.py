from rest_framework import serializers

from players.serializers import PlayerProfileSerializer

from .models import Team, TeamInvitation, TeamLineup, TeamLineupSlot, TeamMembership


class TeamSerializer(serializers.ModelSerializer):
    captain = PlayerProfileSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "captain",
            "city",
            "founded_date",
            "description",
            "squad_size",
            "member_count",
            "matches_total",
            "wins_total",
            "draws_total",
            "losses_total",
            "goals_for_total",
            "goals_against_total",
            "tournaments_total",
            "trophies_total",
        ]
        read_only_fields = [
            "id",
            "slug",
            "captain",
            "member_count",
            "matches_total",
            "wins_total",
            "draws_total",
            "losses_total",
            "goals_for_total",
            "goals_against_total",
            "tournaments_total",
            "trophies_total",
        ]

    def get_member_count(self, obj) -> int:
        return obj.memberships.filter(is_active=True).count()


class TeamMembershipSerializer(serializers.ModelSerializer):
    player = PlayerProfileSerializer(read_only=True)

    class Meta:
        model = TeamMembership
        fields = ["id", "player", "is_active", "created_at", "left_at"]
        read_only_fields = fields


class TeamInvitationSerializer(serializers.ModelSerializer):
    invited_player = PlayerProfileSerializer(read_only=True)
    team = TeamSerializer(read_only=True)

    class Meta:
        model = TeamInvitation
        fields = [
            "id",
            "team",
            "invited_player",
            "invited_by",
            "status",
            "created_at",
            "responded_at",
        ]
        read_only_fields = fields


class InvitePlayerSerializer(serializers.Serializer):
    player_id = serializers.CharField()


class TeamLineupSlotSerializer(serializers.ModelSerializer):
    player = PlayerProfileSerializer(read_only=True)

    class Meta:
        model = TeamLineupSlot
        fields = ["code", "player"]
        read_only_fields = fields


class TeamLineupSerializer(serializers.ModelSerializer):
    slots = TeamLineupSlotSerializer(many=True, read_only=True)

    class Meta:
        model = TeamLineup
        fields = ["formation", "slots"]
        read_only_fields = fields


class SetTeamLineupSerializer(serializers.Serializer):
    # Not a ChoiceField: which formations are valid depends on the
    # team's squad_size, checked in teams.services.set_team_lineup.
    formation = serializers.CharField(max_length=10)
    assignments = serializers.DictField(
        child=serializers.IntegerField(allow_null=True), required=False, default=dict
    )
