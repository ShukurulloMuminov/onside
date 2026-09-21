from django.db import migrations

LEVELS = [
    (1, "Rookie", "🌱", 0),
    (2, "Amateur", "🟢", 20),
    (3, "Player", "⚽", 50),
    (4, "Skilled", "🔥", 100),
    (5, "Pro", "💪", 180),
    (6, "Elite", "⭐", 280),
    (7, "Star", "🌟", 400),
    (8, "Master", "🏅", 550),
    (9, "Champion", "🏆", 750),
    (10, "Legend", "👑", 1000),
]

BADGES = [
    ("Tournament Winner", "🏆", "Turnir g'olibi", True),
    ("MVP", "⭐", "Turnir yoki o'yin MVP'si", True),
    ("Top Scorer", "🔥", "Eng ko'p gol urgan o'yinchi", True),
    ("Best Assist", "🎯", "Eng ko'p gol uzatgan o'yinchi", True),
    ("Best Goalkeeper", "🧤", "Eng yaxshi darvozabon", True),
    ("OnSide Legend", "👑", "Platformaning afsonaviy o'yinchisi", False),
]


def seed(apps, schema_editor):
    Level = apps.get_model("gamification", "Level")
    Badge = apps.get_model("gamification", "Badge")

    for order, name, icon, required_points in LEVELS:
        Level.objects.get_or_create(
            order=order, defaults={"name": name, "icon": icon, "required_points": required_points}
        )

    for name, icon, description, is_automatic in BADGES:
        Badge.objects.get_or_create(
            name=name, defaults={"icon": icon, "description": description, "is_automatic": is_automatic}
        )


def unseed(apps, schema_editor):
    Level = apps.get_model("gamification", "Level")
    Badge = apps.get_model("gamification", "Badge")
    Level.objects.filter(order__in=[o for o, *_ in LEVELS]).delete()
    Badge.objects.filter(name__in=[n for n, *_ in BADGES]).delete()


class Migration(migrations.Migration):
    dependencies = [("gamification", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
