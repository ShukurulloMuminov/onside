from rest_framework import serializers

from .models import PlayerProfile


class PlayerProfileSerializer(serializers.ModelSerializer):
    player_id = serializers.CharField(read_only=True)
    full_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    current_team = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()

    class Meta:
        model = PlayerProfile
        fields = [
            "id",
            "player_id",
            "full_name",
            "username",
            "avatar",
            "city",
            "position",
            "bio",
            "current_team",
            "level",
            "badges",
            "matches_total",
            "wins_total",
            "goals_total",
            "assists_total",
            "mvp_total",
            "yellow_cards_total",
            "red_cards_total",
            "tournaments_total",
            "rating_avg",
        ]
        read_only_fields = [f for f in fields if f not in ("avatar", "city", "position", "bio")]

    def get_full_name(self, obj) -> str:
        return obj.user.get_full_name() or obj.user.username

    def get_username(self, obj) -> str:
        return obj.user.username

    def get_current_team(self, obj) -> dict | None:
        membership = obj.team_memberships.filter(is_active=True).select_related("team").first()
        if not membership:
            return None
        return {"id": membership.team_id, "name": membership.team.name, "slug": membership.team.slug}

    def get_level(self, obj) -> dict | None:
        from gamification.serializers import LevelSerializer
        from gamification.services import get_level_for_player

        level = get_level_for_player(obj)
        return LevelSerializer(level).data if level else None

    def get_badges(self, obj) -> list[dict]:
        from gamification.serializers import PlayerBadgeSerializer

        return PlayerBadgeSerializer(obj.badges.select_related("badge"), many=True).data
