import random

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from matches.models import Match, MatchEvent
from players.models import PlayerProfile
from stats.services import KnockoutService
from teams import services as team_services
from teams.models import Team
from tournaments import services as tournament_services
from tournaments.models import KnockoutRound, Tournament, TournamentAdmin, TournamentStage

DEMO_PASSWORD = "Demo12345!"

# Seed order = registration order below (team 0 is the #1 seed). Bracket
# seeding pairs 1v16, 8v9, 4v13, ... (standard tournament seeding) so the
# favourite meets the toughest remaining opponent as late as possible.
CITY_TEAMS = [
    "Toshkent", "Samarqand", "Buxoro", "Andijon", "Farg'ona", "Namangan",
    "Nukus", "Termez", "Qarshi", "Jizzax", "Guliston", "Navoiy",
    "Urganch", "Xiva", "Angren", "Chirchiq",
]

FIRST_NAMES = [
    "Aziz", "Bekzod", "Davron", "Elyor", "Farrux", "G'ayrat", "Husan", "Ibrohim",
    "Jasur", "Karim", "Laziz", "Muzaffar", "Nodir", "Otabek", "Rustam", "Sardor",
]
LAST_NAMES = [
    "Yusupov", "Tursunov", "Rahimov", "Islomov", "Xolmatov", "Saidov", "Ergashev",
    "Nematov", "Qodirov", "Aliyev", "Ochilov", "Toshev", "Karimov", "Yoldoshev",
    "Nazarov", "Rashidov",
]
POSITIONS = [
    PlayerProfile.Position.GOALKEEPER,
    PlayerProfile.Position.DEFENDER,
    PlayerProfile.Position.MIDFIELDER,
    PlayerProfile.Position.FORWARD,
]


class Command(BaseCommand):
    help = (
        "Seeds a full 16-team knockout-only tournament (Round of 16 -> QF -> SF -> "
        "Final + Third Place) with every match already played, to showcase the "
        "full bracket view."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        admin_user = User.objects.filter(is_superuser=True).order_by("id").first()
        if not admin_user:
            self.stderr.write("No superuser found. Run `python manage.py createsuperuser` first.")
            return

        tournament_admin_user, _ = User.objects.get_or_create(
            username="tournament_admin",
            defaults={"email": "tournament_admin@onside.uz", "first_name": "Nodir", "last_name": "Ergashev"},
        )
        if not tournament_admin_user.has_usable_password():
            tournament_admin_user.set_password(DEMO_PASSWORD)
            tournament_admin_user.save()

        tournament, created = Tournament.objects.get_or_create(
            slug="ozbekiston-havaskorlar-superligasi",
            defaults=dict(
                name="O'zbekiston Havaskorlar Superligasi",
                organizer="OnSide.uz",
                city="Toshkent",
                venue="Milliy Stadion",
                description="16 ta viloyat/shahar jamoasi ishtirokidagi to'liq playoff turniri.",
                format=Tournament.Format.PLAYOFF,
                status=Tournament.Status.REGISTRATION_OPEN,
                max_teams=16,
                qualifiers_per_group=0,
                created_by=admin_user,
            ),
        )
        TournamentAdmin.objects.get_or_create(
            tournament=tournament, user=tournament_admin_user, defaults={"assigned_by": admin_user}
        )

        if not created and tournament.matches.exists():
            self.stdout.write(self.style.WARNING("Big tournament already seeded — skipping."))
            return

        seeds = []  # ordered list of (team, captain_profile, players[])
        for seed_index, city in enumerate(CITY_TEAMS):
            team, captain, roster = self._make_team(seed_index, city)
            seeds.append((team, captain, roster))

        for team, captain, _roster in seeds:
            reg = tournament_services.apply_to_tournament(
                tournament=tournament, team=team, acting_user=captain.user
            )
            tournament_services.review_registration(
                registration=reg, acting_user=tournament_admin_user, approve=True
            )

        KnockoutService.generate_bracket(tournament=tournament, acting_user=tournament_admin_user)

        # seed number (1-indexed, lower = stronger) keyed by team id, so we
        # can resolve every match's "favourite" without needing to know the
        # bracket pairing order ourselves.
        seed_by_team_id = {team.id: i + 1 for i, (team, _c, _r) in enumerate(seeds)}
        roster_by_team_id = {team.id: (captain, roster) for team, captain, roster in seeds}

        stage = TournamentStage.objects.get(tournament=tournament, type=TournamentStage.Type.KNOCKOUT)
        round_order = [
            KnockoutRound.Name.ROUND_OF_16,
            KnockoutRound.Name.QUARTERFINAL,
            KnockoutRound.Name.SEMIFINAL,
            KnockoutRound.Name.FINAL,
        ]

        semifinal_losers = []
        for round_name in round_order:
            matches = list(
                Match.objects.filter(tournament=tournament, knockout_round__name=round_name).order_by("id")
            )
            for match in matches:
                loser_reg = self._play_match(
                    match, seed_by_team_id, roster_by_team_id, tournament_admin_user
                )
                if round_name == KnockoutRound.Name.SEMIFINAL:
                    semifinal_losers.append(loser_reg)

        self._play_third_place(tournament, stage, semifinal_losers, seed_by_team_id, roster_by_team_id, tournament_admin_user)

        self.stdout.write(self.style.SUCCESS("Big tournament seeded: 16 teams, full bracket played out."))
        self.stdout.write(f"  URL: /tournaments/{tournament.slug}")

    def _make_team(self, seed_index: int, city: str):
        players = []
        for slot in range(4):
            p = seed_index * 4 + slot
            username = f"sl_{FIRST_NAMES[p % 16].lower()}{p}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults=dict(
                    email=f"{username}@onside.uz",
                    first_name=FIRST_NAMES[p % 16],
                    last_name=LAST_NAMES[(p // 4) % 16],
                    city=city,
                ),
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            profile, _ = PlayerProfile.objects.get_or_create(
                user=user, defaults={"city": city, "position": POSITIONS[slot]}
            )
            players.append(profile)

        captain = players[2]  # midfielder captains, matches the other seed script's convention
        team_name = f"{city} Superliga"
        existing = Team.objects.filter(name=team_name).first()
        if existing:
            return existing, captain, players
        team = team_services.create_team(creator=captain, name=team_name, city=city)
        for p in players:
            if p.pk != captain.pk:
                inv = team_services.invite_player(team=team, acting_user=captain.user, player_id=p.player_id)
                team_services.respond_to_invitation(invitation=inv, acting_user=p.user, accept=True)
        return team, captain, players

    def _play_match(self, match, seed_by_team_id, roster_by_team_id, acting_user):
        match.refresh_from_db()
        home_team_id = match.home_registration.team_id
        away_team_id = match.away_registration.team_id
        home_seed = seed_by_team_id[home_team_id]
        away_seed = seed_by_team_id[away_team_id]

        favourite_is_home = home_seed < away_seed
        margin = 1 if abs(home_seed - away_seed) > 6 else random.choice([1, 1, 2])
        loser_score = random.choice([0, 0, 1])
        winner_score = loser_score + margin

        home_score, away_score = (winner_score, loser_score) if favourite_is_home else (loser_score, winner_score)

        match.status = Match.Status.FINISHED
        match.home_score = home_score
        match.away_score = away_score
        match.created_by = acting_user
        match.save()

        winner_team_id = home_team_id if favourite_is_home else away_team_id
        winner_reg = match.home_registration if favourite_is_home else match.away_registration
        loser_reg = match.away_registration if favourite_is_home else match.home_registration
        scorer_captain, roster = roster_by_team_id[winner_team_id]
        forward = roster[3]  # the FW slot
        for minute, _ in enumerate(range(winner_score), start=1):
            MatchEvent.objects.create(
                match=match,
                type=MatchEvent.Type.GOAL,
                player=forward if minute > 1 else scorer_captain,
                team_registration=winner_reg,
                minute=minute * 20,
                created_by=acting_user,
            )
        return loser_reg

    def _play_third_place(self, tournament, stage, semifinal_losers, seed_by_team_id, roster_by_team_id, acting_user):
        if len(semifinal_losers) != 2:
            return
        # KnockoutService.advance() already created this match (and slotted
        # in both semifinal losers) via the post_save signal fired while
        # the semifinals above were being played out — just play it out.
        match = Match.objects.get(tournament=tournament, stage=stage, knockout_round__name=KnockoutRound.Name.THIRD_PLACE)
        self._play_match(match, seed_by_team_id, roster_by_team_id, acting_user)
