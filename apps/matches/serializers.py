from rest_framework import serializers
from .models import Match, MatchEvent, PlayerMatchStat
from apps.accounts.serializers import UserListSerializer
from apps.teams.serializers import TeamListSerializer


class MatchEventSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.full_name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = MatchEvent
        fields = ['id', 'player', 'player_name', 'team', 'team_name',
                  'event_type', 'event_type_display', 'minute', 'description', 'created_at']
        read_only_fields = ['created_at']


class MatchEventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchEvent
        fields = ['player', 'team', 'event_type', 'minute', 'description']

    def validate(self, attrs):
        match = self.context['match']
        # O'yinchi shu jamoada ekanligini tekshirish
        team = attrs['team']
        player = attrs['player']
        from apps.teams.models import TeamMembership
        if not TeamMembership.objects.filter(team=team, player=player, is_active=True).exists():
            raise serializers.ValidationError({'player': 'Bu o\'yinchi shu jamoada emas'})
        # Jamoa shu o'yinda ekanligini tekshirish
        if team not in [match.home_team, match.away_team]:
            raise serializers.ValidationError({'team': 'Bu jamoa shu o\'yinda qatnashmaydi'})
        return attrs


class PlayerMatchStatSerializer(serializers.ModelSerializer):
    player = UserListSerializer(read_only=True)
    player_id = serializers.IntegerField(write_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = PlayerMatchStat
        fields = ['id', 'player', 'player_id', 'team', 'team_name', 'goals',
                  'assists', 'yellow_cards', 'red_cards', 'minutes_played',
                  'is_starting', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class PlayerMatchStatBulkSerializer(serializers.Serializer):
    """Bir o'yindagi barcha o'yinchilar statistikasini bir vaqtda kiritish"""
    stats = serializers.ListField(child=serializers.DictField())

    def validate_stats(self, stats_data):
        validated = []
        for item in stats_data:
            player_id = item.get('player_id')
            team_id = item.get('team')
            if not player_id or not team_id:
                raise serializers.ValidationError('player_id va team majburiy')
            validated.append(item)
        return validated


class MatchListSerializer(serializers.ModelSerializer):
    home_team_name = serializers.CharField(source='home_team.name', read_only=True)
    home_team_logo = serializers.ImageField(source='home_team.logo', read_only=True)
    away_team_name = serializers.CharField(source='away_team.name', read_only=True)
    away_team_logo = serializers.ImageField(source='away_team.logo', read_only=True)
    tournament_name = serializers.CharField(source='tournament.name', read_only=True)
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Match
        fields = ['id', 'tournament', 'tournament_name', 'home_team', 'home_team_name',
                  'home_team_logo', 'away_team', 'away_team_name', 'away_team_logo',
                  'home_score', 'away_score', 'stage', 'stage_display',
                  'status', 'status_display', 'match_date', 'location']


class MatchDetailSerializer(serializers.ModelSerializer):
    home_team = TeamListSerializer(read_only=True)
    away_team = TeamListSerializer(read_only=True)
    match_admin = UserListSerializer(read_only=True)
    events = MatchEventSerializer(many=True, read_only=True)
    player_stats = PlayerMatchStatSerializer(many=True, read_only=True)
    stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    result = serializers.ReadOnlyField()

    class Meta:
        model = Match
        fields = '__all__'


class MatchCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ['tournament', 'group', 'home_team', 'away_team',
                  'stage', 'match_date', 'location', 'match_admin', 'notes']

    def validate(self, attrs):
        if attrs.get('home_team') == attrs.get('away_team'):
            raise serializers.ValidationError('Bir xil jamoalar o\'ynay olmaydi')
        return attrs


class MatchScoreUpdateSerializer(serializers.Serializer):
    """O'yin hisobini yangilash"""
    home_score = serializers.IntegerField(min_value=0)
    away_score = serializers.IntegerField(min_value=0)
    status = serializers.ChoiceField(choices=['live', 'finished', 'scheduled'], required=False)


class MatchStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[s[0] for s in Match.Status.choices])
