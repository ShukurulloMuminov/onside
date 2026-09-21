from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("OnSide profile", {"fields": ("phone", "city")}),
    )
    list_display = ("username", "email", "phone", "city", "is_staff", "is_superuser")
    search_fields = ("username", "email", "phone", "first_name", "last_name")
