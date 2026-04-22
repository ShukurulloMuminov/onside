from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT tokenga qo'shimcha ma'lumotlar qo'shish"""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role
        token['full_name'] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserProfileSerializer(self.user).data
        return data


class UserRegisterSerializer(serializers.ModelSerializer):
    """Oddiy ro'yxatdan o'tish - faqat PLAYER roli"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',
                  'phone', 'password', 'password2', 'position', 'date_of_birth']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Parollar mos kelmaydi."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.role = User.Role.PLAYER
        user.set_password(password)
        user.save()
        return user


class AdminCreateUserSerializer(serializers.ModelSerializer):
    """Admin tomonidan foydalanuvchi yaratish - rol va parol beriladi"""
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',
                  'phone', 'password', 'role', 'position', 'date_of_birth']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Foydalanuvchi profili"""
    full_name = serializers.ReadOnlyField()
    total_goals = serializers.SerializerMethodField()
    total_assists = serializers.SerializerMethodField()
    total_matches = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'full_name', 'phone', 'avatar', 'bio', 'role',
                  'position', 'date_of_birth', 'total_goals',
                  'total_assists', 'total_matches', 'created_at']
        read_only_fields = ['id', 'role', 'created_at']

    def get_total_goals(self, obj):
        return obj.player_stats.aggregate(
            total=models.Sum('goals')
        )['total'] or 0

    def get_total_assists(self, obj):
        return obj.player_stats.aggregate(
            total=models.Sum('assists')
        )['total'] or 0

    def get_total_matches(self, obj):
        return obj.player_stats.count()


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Profilni yangilash"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar',
                  'bio', 'position', 'date_of_birth']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Yangi parollar mos kelmaydi."})
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """Admin uchun foydalanuvchilar ro'yxati"""
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email', 'phone',
                  'role', 'position', 'is_active', 'created_at']


# Fix circular import
from django.db import models
