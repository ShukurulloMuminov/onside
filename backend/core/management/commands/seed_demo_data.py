from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from matches.models import Match, MatchEvent
from players.models import PlayerProfile
from teams import services as team_services
from tournaments import services as tournament_services
from tournaments.models import Tournament, TournamentAdmin
from stats.services import KnockoutService

DEMO_PASSWORD = "Demo12345!"

TEAMS = [
    {
        "name": "Qarshi Yulduzlari",
        "city": "Qarshi",
        "players": [
            ("ali_karimov", "Ali", "Karimov", PlayerProfile.Position.MIDFIELDER, True),
            ("vali_toshev", "Vali", "Toshev", PlayerProfile.Position.FORWARD, False),
            ("bekzod_rahimov", "Bekzod", "Rahimov", PlayerProfile.Position.DEFENDER, False),
            ("sardor_yusupov", "Sardor", "Yusupov", PlayerProfile.Position.GOALKEEPER, False),
        ],
    },
    {
        "name": "Termez Olovi",
        "city": "Termez",
        "players": [
            ("otabek_yoldoshev", "Otabek", "Yoldoshev", PlayerProfile.Position.MIDFIELDER, True),
            ("jasur_nazarov", "Jasur", "Nazarov", PlayerProfile.Position.FORWARD, False),
            ("farrux_islomov", "Farrux", "Islomov", PlayerProfile.Position.DEFENDER, False),
            ("sherzod_qodirov", "Sherzod", "Qodirov", PlayerProfile.Position.GOALKEEPER, False),
        ],
    },
    {
        "name": "Buxoro Sharqi",
        "city": "Buxoro",
        "players": [
            ("ulugbek_saidov", "Ulugbek", "Saidov", PlayerProfile.Position.MIDFIELDER, True),
            ("davron_xolmatov", "Davron", "Xolmatov", PlayerProfile.Position.FORWARD, False),
            ("rustam_ergashev", "Rustam", "Ergashev", PlayerProfile.Position.DEFENDER, False),
            ("aziz_nematov", "Aziz", "Nematov", PlayerProfile.Position.GOALKEEPER, False),
        ],
    },
    {
        "name": "Nukus Tulporlari",
        "city": "Nukus",
        "players": [
            ("sanjar_yusupov", "Sanjar", "Yusupov", PlayerProfile.Position.MIDFIELDER, True),
            ("bobur_aliyev", "Bobur", "Aliyev", PlayerProfile.Position.FORWARD, False),
            ("elyor_tashkentov", "Elyor", "Tashkentov", PlayerProfile.Position.DEFENDER, False),
            ("diyor_rashidov", "Diyor", "Rashidov", PlayerProfile.Position.GOALKEEPER, False),
        ],
    },
]

# Results are keyed by (team_a_name, team_b_name) rather than match
# index/home-away, because tournaments.services.generate_groups()
# deliberately shuffles teams before pairing them (real fixture fairness)
# — so which generated Match object ends up as index 0, and which side
# of it is "home", isn't predictable from this script. Orientation is
# resolved against the real Match at seed time (see _apply_result).
# events: list of (type, username, minute, "a" | "b")
GROUP_RESULTS = [
    ("Qarshi Yulduzlari", "Nukus Tulporlari", 3, 1, [
        ("goal", "vali_toshev", 12, "a"),
        ("assist", "ali_karimov", 12, "a"),
        ("goal", "vali_toshev", 39, "a"),
        ("goal", "ali_karimov", 60, "a"),
        ("goal", "bobur_aliyev", 70, "b"),
        ("yellow_card", "elyor_tashkentov", 75, "b"),
        ("mvp", "vali_toshev", 90, "a"),
    ]),
    ("Termez Olovi", "Buxoro Sharqi", 1, 1, [
        ("goal", "jasur_nazarov", 20, "a"),
        ("assist", "otabek_yoldoshev", 20, "a"),
        ("goal", "davron_xolmatov", 65, "b"),
    ]),
    ("Buxoro Sharqi", "Qarshi Yulduzlari", 0, 2, [
        ("goal", "vali_toshev", 30, "b"),
        ("goal", "ali_karimov", 82, "b"),
        ("red_card", "rustam_ergashev", 78, "a"),
    ]),
    ("Termez Olovi", "Nukus Tulporlari", 4, 0, [
        ("goal", "jasur_nazarov", 5, "a"),
        ("goal", "otabek_yoldoshev", 25, "a"),
        ("assist", "jasur_nazarov", 25, "a"),
        ("goal", "jasur_nazarov", 51, "a"),
        ("assist", "otabek_yoldoshev", 51, "a"),
        ("goal", "farrux_islomov", 88, "a"),
        ("mvp", "jasur_nazarov", 90, "a"),
    ]),
    ("Qarshi Yulduzlari", "Termez Olovi", 1, 0, [
        ("goal", "vali_toshev", 44, "a"),
        ("yellow_card", "bekzod_rahimov", 60, "a"),
    ]),
    ("Buxoro Sharqi", "Nukus Tulporlari", 3, 2, [
        ("goal", "davron_xolmatov", 8, "a"),
        ("goal", "ulugbek_saidov", 33, "a"),
        ("goal", "bobur_aliyev", 40, "b"),
        ("goal", "davron_xolmatov", 70, "a"),
        ("goal", "bobur_aliyev", 85, "b"),
    ]),
]

# Qarshi Yulduzlari top the group (9 pts) so KnockoutService seeds them
# as the #1 qualifier — which it always places as the home side of a
# 2-team bracket final — so the final's orientation *is* predictable.
FINAL_RESULT = (2, 1, [
    ("goal", "vali_toshev", 15, 0),
    ("assist", "ali_karimov", 15, 0),
    ("goal", "jasur_nazarov", 40, 1),
    ("goal", "vali_toshev", 77, 0),
    ("mvp", "vali_toshev", 90, 0),
])


class Command(BaseCommand):
    help = "Seeds a realistic demo tournament (teams, players, matches, events) for frontend development."

    @transaction.atomic
    def handle(self, *args, **options):
        admin_user = User.objects.filter(is_superuser=True).order_by("id").first()
        if not admin_user:
            self.stderr.write(
                "No superuser found. Run `python manage.py createsuperuser` first."
            )
            return

        tournament_admin_user, _ = User.objects.get_or_create(
            username="tournament_admin",
            defaults={"email": "tournament_admin@onside.uz", "first_name": "Nodir", "last_name": "Ergashev"},
        )
        if not tournament_admin_user.has_usable_password():
            tournament_admin_user.set_password(DEMO_PASSWORD)
            tournament_admin_user.save()

        free_agent = self._get_or_create_player(
            "jahongir_ochilov", "Jahongir", "Ochilov", "Toshkent", PlayerProfile.Position.MIDFIELDER
        )
        self.stdout.write(f"Free agent ready: {free_agent}")

        teams = []
        for team_def in TEAMS:
            captain_username = next(u for u, *_r, is_cap in team_def["players"] if is_cap)
            captain_profile = None
            member_profiles = []
            for username, first, last, position, is_captain in team_def["players"]:
                profile = self._get_or_create_player(username, first, last, team_def["city"], position)
                member_profiles.append(profile)
                if is_captain:
                    captain_profile = profile

            team, created = self._get_or_create_team(team_def["name"], team_def["city"], captain_profile)
            if created:
                for profile in member_profiles:
                    if profile.pk == captain_profile.pk:
                        continue
                    invitation = team_services.invite_player(
                        team=team, acting_user=captain_profile.user, player_id=profile.player_id
                    )
                    team_services.respond_to_invitation(
                        invitation=invitation, acting_user=profile.user, accept=True
                    )
            teams.append(team)
            self.stdout.write(f"Team ready: {team} (captain {captain_profile})")

        tournament, created = Tournament.objects.get_or_create(
            slug="qashqadaryo-viloyat-kubogi-2026",
            defaults=dict(
                name="Qashqadaryo Viloyat Kubogi 2026",
                organizer="OnSide.uz",
                city="Qarshi",
                venue="Qarshi Markaziy Stadioni",
                description="Qashqadaryo viloyati havaskor futbolchilari uchun yillik kubok turniri.",
                format=Tournament.Format.GROUP_PLAYOFF,
                status=Tournament.Status.REGISTRATION_OPEN,
                max_teams=4,
                groups_count=1,
                teams_per_group=4,
                qualifiers_per_group=2,
                created_by=admin_user,
            ),
        )
        TournamentAdmin.objects.get_or_create(
            tournament=tournament, user=tournament_admin_user, defaults={"assigned_by": admin_user}
        )
        self.stdout.write(f"Tournament ready: {tournament} (status={tournament.status})")

        if not created and tournament.matches.exists():
            self.stdout.write(self.style.WARNING("Tournament already has matches — skipping fixture generation."))
            self.stdout.write(self.style.SUCCESS("Demo data already present."))
            return

        for team in teams:
            if not tournament.registrations.filter(team=team).exists():
                tournament_services.apply_to_tournament(
                    tournament=tournament, team=team, acting_user=team.captain.user
                )
        for registration in tournament.registrations.all():
            tournament_services.review_registration(
                registration=registration, acting_user=tournament_admin_user, approve=True
            )

        tournament_services.generate_groups(tournament=tournament, acting_user=tournament_admin_user)

        group_matches = list(
            tournament.matches.filter(group__isnull=False).select_related(
                "home_registration__team", "away_registration__team"
            )
        )
        matches_by_pair = {
            frozenset([m.home_registration.team.name, m.away_registration.team.name]): m
            for m in group_matches
        }
        username_to_profile = {}
        for team_def in TEAMS:
            for username, *_rest in team_def["players"]:
                username_to_profile[username] = PlayerProfile.objects.get(user__username=username)

        for team_a_name, team_b_name, score_a, score_b, events in GROUP_RESULTS:
            match = matches_by_pair[frozenset([team_a_name, team_b_name])]
            a_is_home = match.home_registration.team.name == team_a_name
            reg_by_marker = (
                {"a": match.home_registration, "b": match.away_registration}
                if a_is_home
                else {"a": match.away_registration, "b": match.home_registration}
            )
            match.status = Match.Status.FINISHED
            match.home_score = score_a if a_is_home else score_b
            match.away_score = score_b if a_is_home else score_a
            match.created_by = tournament_admin_user
            match.save()
            for event_type, username, minute, marker in events:
                MatchEvent.objects.create(
                    match=match,
                    type=event_type,
                    player=username_to_profile[username],
                    team_registration=reg_by_marker[marker],
                    minute=minute,
                    created_by=tournament_admin_user,
                )

        KnockoutService.generate_bracket(tournament=tournament, acting_user=tournament_admin_user)

        final_match = tournament.matches.filter(knockout_round__name="final").first()
        home_score, away_score, events = FINAL_RESULT
        registrations = [final_match.home_registration, final_match.away_registration]
        final_match.status = Match.Status.FINISHED
        final_match.home_score = home_score
        final_match.away_score = away_score
        final_match.created_by = tournament_admin_user
        final_match.save()
        for event_type, username, minute, team_idx in events:
            MatchEvent.objects.create(
                match=final_match,
                type=event_type,
                player=username_to_profile[username],
                team_registration=registrations[team_idx],
                minute=minute,
                created_by=tournament_admin_user,
            )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write(f"  Tournament admin login: tournament_admin / {DEMO_PASSWORD}")
        self.stdout.write(f"  Player logins: <username> / {DEMO_PASSWORD} (e.g. vali_toshev)")

    def _get_or_create_player(self, username, first_name, last_name, city, position):
        user, created = User.objects.get_or_create(
            username=username,
            defaults=dict(
                email=f"{username}@onside.uz",
                first_name=first_name,
                last_name=last_name,
                city=city,
            ),
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        profile, _ = PlayerProfile.objects.get_or_create(
            user=user, defaults={"city": city, "position": position}
        )
        return profile

    def _get_or_create_team(self, name, city, captain_profile):
        from teams.models import Team

        existing = Team.objects.filter(name=name).first()
        if existing:
            return existing, False
        team = team_services.create_team(creator=captain_profile, name=name, city=city)
        return team, True
