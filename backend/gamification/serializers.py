from rest_framework import serializers

from .models import Badge, Level, PlayerBadge


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ["id", "order", "name", "icon", "description", "required_points"]
        read_only_fields = ["id"]


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["id", "name", "icon", "description", "criteria", "is_automatic"]
        read_only_fields = ["id"]


class PlayerBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = PlayerBadge
        fields = ["id", "badge", "created_at"]
        read_only_fields = fields


class AwardBadgeSerializer(serializers.Serializer):
    player_id = serializers.CharField()
