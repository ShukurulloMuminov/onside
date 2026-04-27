from rest_framework import serializers
from .models import Team, TeamMembership, TeamInvitation
from apps.accounts.serializers import UserListSerializer


class TeamMembershipSerializer(serializers.ModelSerializer):
    player = UserListSerializer(read_only=True)
    player_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = TeamMembership
        fields = ['id', 'player', 'player_id', 'role', 'jersey_number', 'joined_at', 'is_active']
        read_only_fields = ['joined_at']


class TeamListSerializer(serializers.ModelSerializer):
    captain_name = serializers.CharField(source='captain.full_name', read_only=True)
    players_count = serializers.ReadOnlyField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'short_name', 'logo', 'city',
                  'captain_name', 'players_count', 'is_active', 'created_at']


class TeamDetailSerializer(serializers.ModelSerializer):
    captain = UserListSerializer(read_only=True)
    members = serializers.SerializerMethodField()
    players_count = serializers.ReadOnlyField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'short_name', 'logo', 'banner', 'description',
                  'city', 'founded_year', 'captain', 'members', 'players_count',
                  'is_active', 'created_at', 'updated_at']

    def get_members(self, obj):
        active_members = obj.memberships.filter(is_active=True).select_related('player')
        return TeamMembershipSerializer(active_members, many=True).data


class TeamCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['name', 'short_name', 'logo', 'banner',
                  'description', 'city', 'founded_year']


class TeamInvitationSerializer(serializers.ModelSerializer):
    invited_player = UserListSerializer(read_only=True)
    invited_player_id = serializers.IntegerField(write_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = TeamInvitation
        fields = ['id', 'team', 'team_name', 'invited_by', 'invited_player',
                  'invited_player_id', 'status', 'message', 'created_at', 'responded_at']
        read_only_fields = ['team', 'invited_by', 'status', 'created_at', 'responded_at']


class InvitationResponseSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['accept', 'reject'])
    jersey_number = serializers.IntegerField(required=False, allow_null=True)


class AddPlayerToTeamSerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    role = serializers.ChoiceField(
        choices=['captain', 'vice_captain', 'player'],
        default='player'
    )
    jersey_number = serializers.IntegerField(required=False, allow_null=True)


class TeamInviteSerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    message = serializers.CharField(required=False, default='')