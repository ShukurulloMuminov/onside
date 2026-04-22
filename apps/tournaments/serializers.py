from rest_framework import serializers
from .models import Tournament, TournamentGroup, TournamentRegistration
from apps.accounts.serializers import UserListSerializer


class TournamentGroupSerializer(serializers.ModelSerializer):
    teams_count = serializers.SerializerMethodField()

    class Meta:
        model = TournamentGroup
        fields = ['id', 'name', 'teams_count']

    def get_teams_count(self, obj):
        return obj.teams.filter(status='approved').count()


class TournamentListSerializer(serializers.ModelSerializer):
    """Turnirlar ro'yxati uchun"""
    teams_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    class Meta:
        model = Tournament
        fields = ['id', 'name', 'logo', 'format', 'status', 'max_teams',
                  'teams_count', 'start_date', 'end_date', 'location',
                  'created_by_name', 'created_at']

    def get_teams_count(self, obj):
        return obj.registrations.filter(status='approved').count()


class TournamentDetailSerializer(serializers.ModelSerializer):
    """Turnir to'liq ma'lumotlari"""
    groups = TournamentGroupSerializer(many=True, read_only=True)
    teams_count = serializers.SerializerMethodField()
    admins = UserListSerializer(many=True, read_only=True)
    created_by = UserListSerializer(read_only=True)

    class Meta:
        model = Tournament
        fields = '__all__'

    def get_teams_count(self, obj):
        return obj.registrations.filter(status='approved').count()


class TournamentCreateUpdateSerializer(serializers.ModelSerializer):
    admin_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Tournament
        fields = ['name', 'description', 'logo', 'banner', 'format',
                  'max_teams', 'min_players_per_team', 'max_players_per_team',
                  'start_date', 'end_date', 'location', 'prize_info', 'rules',
                  'win_points', 'draw_points', 'loss_points', 'admin_ids']

    def create(self, validated_data):
        admin_ids = validated_data.pop('admin_ids', [])
        tournament = Tournament.objects.create(**validated_data)
        if admin_ids:
            from apps.accounts.models import User
            admins = User.objects.filter(id__in=admin_ids, role__in=['tournament_admin', 'superadmin'])
            tournament.admins.set(admins)
        return tournament

    def update(self, instance, validated_data):
        admin_ids = validated_data.pop('admin_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if admin_ids is not None:
            from apps.accounts.models import User
            admins = User.objects.filter(id__in=admin_ids, role__in=['tournament_admin', 'superadmin'])
            instance.admins.set(admins)
        return instance


class TournamentRegistrationSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    team_logo = serializers.ImageField(source='team.logo', read_only=True)
    captain_name = serializers.CharField(source='team.captain.full_name', read_only=True)

    class Meta:
        model = TournamentRegistration
        fields = ['id', 'team', 'team_name', 'team_logo', 'captain_name',
                  'group', 'status', 'registered_at', 'approved_at', 'note']
        read_only_fields = ['status', 'registered_at', 'approved_at']


class RegistrationApproveSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    group_id = serializers.IntegerField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True)


class TournamentStandingSerializer(serializers.Serializer):
    """Turnir jadvali"""
    team_id = serializers.IntegerField()
    team_name = serializers.CharField()
    team_logo = serializers.ImageField()
    played = serializers.IntegerField()
    won = serializers.IntegerField()
    drawn = serializers.IntegerField()
    lost = serializers.IntegerField()
    goals_for = serializers.IntegerField()
    goals_against = serializers.IntegerField()
    goal_difference = serializers.IntegerField()
    points = serializers.IntegerField()
