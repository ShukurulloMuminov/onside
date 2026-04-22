from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.utils import timezone
from django.db.models import Q, Sum, Count

from .models import Tournament, TournamentGroup, TournamentRegistration
from .serializers import (
    TournamentListSerializer,
    TournamentDetailSerializer,
    TournamentCreateUpdateSerializer,
    TournamentRegistrationSerializer,
    RegistrationApproveSerializer,
    TournamentGroupSerializer,
    TournamentStandingSerializer,
)
from apps.accounts.permissions import IsTournamentAdmin, IsSuperAdmin


class TournamentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/tournaments/        - Barcha turnirlar (public)
    POST /api/v1/tournaments/        - Yangi turnir (admin)
    """
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'format']
    search_fields = ['name', 'location']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsTournamentAdmin()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TournamentCreateUpdateSerializer
        return TournamentListSerializer

    def get_queryset(self):
        return Tournament.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TournamentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/tournaments/{id}/  - Turnir ma'lumotlari (public)
    PUT    /api/v1/tournaments/{id}/  - Yangilash (admin)
    DELETE /api/v1/tournaments/{id}/  - O'chirish (superadmin)
    """
    queryset = Tournament.objects.all()

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        if self.request.method == 'DELETE':
            return [IsSuperAdmin()]
        return [IsTournamentAdmin()]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TournamentCreateUpdateSerializer
        return TournamentDetailSerializer


class TournamentStatusView(APIView):
    """
    POST /api/v1/tournaments/{id}/status/
    Turnir statusini o'zgartirish
    """
    permission_classes = [IsTournamentAdmin]

    def post(self, request, pk):
        try:
            tournament = Tournament.objects.get(pk=pk)
        except Tournament.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if not tournament.is_admin(request.user):
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        valid_statuses = [s[0] for s in Tournament.Status.choices]
        if new_status not in valid_statuses:
            return Response({'error': f'Noto\'g\'ri status. Mumkin: {valid_statuses}'}, status=status.HTTP_400_BAD_REQUEST)

        tournament.status = new_status
        tournament.save()
        return Response({'message': f'Status "{tournament.get_status_display()}" ga o\'zgartirildi'})


class TournamentRegistrationListView(generics.ListCreateAPIView):
    """
    GET  /api/v1/tournaments/{id}/registrations/   - Ro'yxatlar (admin)
    POST /api/v1/tournaments/{id}/registrations/   - Ro'yxatga olish (jamoa sardori)
    """
    serializer_class = TournamentRegistrationSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsTournamentAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        return TournamentRegistration.objects.filter(
            tournament_id=self.kwargs['pk']
        ).select_related('team', 'team__captain')

    def create(self, request, *args, **kwargs):
        tournament = Tournament.objects.get(pk=kwargs['pk'])

        if tournament.status != 'registration':
            return Response({'error': 'Turnir hozir ro\'yxatga olish bosqichida emas'}, status=status.HTTP_400_BAD_REQUEST)

        team_id = request.data.get('team')
        from apps.teams.models import Team
        try:
            team = Team.objects.get(pk=team_id)
        except Team.DoesNotExist:
            return Response({'error': 'Jamoa topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        # Faqat jamoa sardori ro'yxatga olishi mumkin
        if team.captain != request.user:
            return Response({'error': 'Faqat jamoa sardori ro\'yxatga olishi mumkin'}, status=status.HTTP_403_FORBIDDEN)

        if TournamentRegistration.objects.filter(tournament=tournament, team=team).exists():
            return Response({'error': 'Bu jamoa allaqachon ro\'yxatga olingan'}, status=status.HTTP_400_BAD_REQUEST)

        reg = TournamentRegistration.objects.create(tournament=tournament, team=team)
        return Response(TournamentRegistrationSerializer(reg).data, status=status.HTTP_201_CREATED)


class RegistrationApproveView(APIView):
    """
    POST /api/v1/tournaments/{id}/registrations/{reg_id}/approve/
    Ro'yxatni tasdiqlash yoki rad etish (admin)
    """
    permission_classes = [IsTournamentAdmin]

    def post(self, request, pk, reg_id):
        try:
            reg = TournamentRegistration.objects.get(pk=reg_id, tournament_id=pk)
        except TournamentRegistration.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        serializer = RegistrationApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reg.status = serializer.validated_data['status']
        if serializer.validated_data['status'] == 'approved':
            reg.approved_at = timezone.now()
            group_id = serializer.validated_data.get('group_id')
            if group_id:
                reg.group_id = group_id
        reg.note = serializer.validated_data.get('note', '')
        reg.save()

        return Response({
            'message': f'{reg.team.name} {reg.get_status_display().lower()}',
            'registration': TournamentRegistrationSerializer(reg).data
        })


class TournamentGroupView(generics.ListCreateAPIView):
    """
    GET  /api/v1/tournaments/{id}/groups/   - Guruhlar
    POST /api/v1/tournaments/{id}/groups/   - Guruh yaratish (admin)
    """
    serializer_class = TournamentGroupSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsTournamentAdmin()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        return TournamentGroup.objects.filter(tournament_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        tournament = Tournament.objects.get(pk=self.kwargs['pk'])
        serializer.save(tournament=tournament)


class TournamentStandingsView(APIView):
    """
    GET /api/v1/tournaments/{id}/standings/
    Turnir jadvali (liga formati uchun)
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            tournament = Tournament.objects.get(pk=pk)
        except Tournament.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        from apps.matches.models import Match
        approved_teams = tournament.registrations.filter(
            status='approved'
        ).select_related('team')

        standings = []
        for reg in approved_teams:
            team = reg.team
            home_matches = Match.objects.filter(
                tournament=tournament, home_team=team, status='finished'
            )
            away_matches = Match.objects.filter(
                tournament=tournament, away_team=team, status='finished'
            )

            played = home_matches.count() + away_matches.count()
            won = draw = lost = gf = ga = 0

            for m in home_matches:
                gf += m.home_score
                ga += m.away_score
                if m.home_score > m.away_score:
                    won += 1
                elif m.home_score == m.away_score:
                    draw += 1
                else:
                    lost += 1

            for m in away_matches:
                gf += m.away_score
                ga += m.home_score
                if m.away_score > m.home_score:
                    won += 1
                elif m.away_score == m.home_score:
                    draw += 1
                else:
                    lost += 1

            points = won * tournament.win_points + draw * tournament.draw_points + lost * tournament.loss_points

            standings.append({
                'team_id': team.id,
                'team_name': team.name,
                'team_logo': request.build_absolute_uri(team.logo.url) if team.logo else None,
                'played': played,
                'won': won,
                'drawn': draw,
                'lost': lost,
                'goals_for': gf,
                'goals_against': ga,
                'goal_difference': gf - ga,
                'points': points,
            })

        standings.sort(key=lambda x: (-x['points'], -x['goal_difference'], -x['goals_for']))
        return Response(standings)
