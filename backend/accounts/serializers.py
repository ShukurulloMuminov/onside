from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    """Creates the User and its PlayerProfile together in one call, since
    the spec's registration form collects position/city/avatar (player
    profile fields) alongside the account fields in a single step."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    position = serializers.ChoiceField(
        choices=[], required=False, allow_blank=True, write_only=True
    )
    avatar = serializers.ImageField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "password",
            "first_name",
            "last_name",
            "city",
            "position",
            "avatar",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Lazy import to avoid an accounts <-> players circular import
        # at module load time.
        from players.models import PlayerProfile

        self.fields["position"].choices = PlayerProfile.Position.choices

    @transaction.atomic
    def create(self, validated_data):
        from players.models import PlayerProfile

        position = validated_data.pop("position", "")
        avatar = validated_data.pop("avatar", None)
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        PlayerProfile.objects.create(
            user=user,
            city=validated_data.get("city", ""),
            position=position,
            avatar=avatar,
        )
        return user


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "first_name",
            "last_name",
            "city",
            "role",
            "is_superuser",
        ]
        read_only_fields = fields

    def get_role(self, obj) -> str:
        if obj.is_superuser:
            return "super_admin"
        if obj.is_tournament_admin:
            return "tournament_admin"
        return "player"
