from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'full_name', 'role', 'phone', 'position', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'position']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']
    ordering = ['-created_at']

    fieldsets = UserAdmin.fieldsets + (
        ('Onside UZ', {'fields': ('role', 'phone', 'avatar', 'bio', 'date_of_birth', 'position')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Onside UZ', {'fields': ('role', 'phone', 'position')}),
    )
