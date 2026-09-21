from django.contrib import admin

from .models import Badge, Level, PlayerBadge


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("order", "icon", "name", "required_points")
    ordering = ["order"]


class PlayerBadgeInline(admin.TabularInline):
    model = PlayerBadge
    extra = 0
    readonly_fields = ("awarded_by",)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("icon", "name", "is_automatic")
    search_fields = ("name",)
    inlines = [PlayerBadgeInline]


@admin.register(PlayerBadge)
class PlayerBadgeAdmin(admin.ModelAdmin):
    list_display = ("player", "badge", "awarded_by", "created_at")
    list_filter = ("badge",)
