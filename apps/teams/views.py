from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from django.utils import timezone

from .models import Team, TeamMembership, TeamInvitation
from .serializers import (
    TeamListSerializer,
    TeamDetailSerializer,
    TeamCreateUpdateSerializer,
    TeamMembershipSerializer,
    TeamInvitationSerializer,
    InvitationResponseSerializer,
    AddPlayerToTeamSerializer,
    TeamInviteSerializer,
)
from apps.accounts.permissions import IsTournamentAdmin
from apps.accounts.models import User


class TeamListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/teams/     - Barcha jamoalar (public)
    POST /api/v1/teams/     - Jamoa yaratish (istalgan o'yinchi)
    """
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['city', 'is_active']
    search_fields = ['name', 'short_name', 'city']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TeamCreateUpdateSerializer
        return TeamListSerializer

    def get_queryset(self):
        return Team.objects.filter(is_active=True)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.save(captain=request.user)

        # Yaratuvchi avtomatik captain bo'ladi
        TeamMembership.objects.create(
            team=team,
            player=request.user,
            role='captain'
        )
        return Response(TeamDetailSerializer(team).data, status=status.HTTP_201_CREATED)


class TeamDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/teams/{id}/   - Jamoa ma'lumotlari (public)
    PUT    /api/v1/teams/{id}/   - Yangilash (captain/admin)
    DELETE /api/v1/teams/{id}/   - O'chirish (captain/admin)
    """
    queryset = Team.objects.all()

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TeamCreateUpdateSerializer
        return TeamDetailSerializer

    def update(self, request, *args, **kwargs):
        team = self.get_object()
        if team.captain != request.user and not request.user.is_tournament_admin:
            return Response({'error': 'Faqat jamoa sardori o\'zgartira oladi'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        team = self.get_object()
        if team.captain != request.user and not request.user.is_tournament_admin:
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)
        team.is_active = False
        team.save()
        return Response({'message': 'Jamoa o\'chirildi'})


class TeamMembersView(APIView):
    """
    GET    /api/v1/teams/{id}/members/              - A'zolar ro'yxati
    POST   /api/v1/teams/{id}/members/              - A'zo qo'shish (captain/admin)
    DELETE /api/v1/teams/{id}/members/{player_id}/  - A'zoni chiqarish
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request, pk):
        try:
            team = Team.objects.get(pk=pk)
        except Team.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)
        members = team.memberships.filter(is_active=True).select_related('player')
        return Response(TeamMembershipSerializer(members, many=True).data)

    def post(self, request, pk):
        """Captain yoki admin to'g'ridan-to'g'ri a'zo qo'shadi"""
        try:
            team = Team.objects.get(pk=pk)
        except Team.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if team.captain != request.user and not request.user.is_tournament_admin:
            return Response({'error': 'Faqat jamoa sardori a\'zo qo\'sha oladi'}, status=status.HTTP_403_FORBIDDEN)

        serializer = AddPlayerToTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            player = User.objects.get(pk=serializer.validated_data['player_id'])
        except User.DoesNotExist:
            return Response({'error': 'O\'yinchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if team.memberships.filter(player=player, is_active=True).exists():
            return Response({'error': 'Bu o\'yinchi allaqachon jamoada'}, status=status.HTTP_400_BAD_REQUEST)

        membership = TeamMembership.objects.create(
            team=team,
            player=player,
            role=serializer.validated_data.get('role', 'player'),
            jersey_number=serializer.validated_data.get('jersey_number')
        )
        return Response(TeamMembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


class TeamMemberRemoveView(APIView):
    """
    DELETE /api/v1/teams/{id}/members/{player_id}/
    A'zoni jamoadan chiqarish
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, player_id):
        try:
            team = Team.objects.get(pk=pk)
        except Team.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        # Faqat captain yoki admin chiqarishi mumkin, yoki o'zi ketishi
        if team.captain != request.user and not request.user.is_tournament_admin and request.user.id != player_id:
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        membership = team.memberships.filter(player_id=player_id, is_active=True).first()
        if not membership:
            return Response({'error': 'Bu o\'yinchi jamoada emas'}, status=status.HTTP_404_NOT_FOUND)

        if player_id == team.captain.id:
            return Response({'error': 'Sardorni jamoadan chiqarib bo\'lmaydi'}, status=status.HTTP_400_BAD_REQUEST)

        membership.is_active = False
        membership.left_at = timezone.now()
        membership.save()
        return Response({'message': 'O\'yinchi jamoadan chiqarildi'})


class TeamChangeCaptainView(APIView):
    """
    POST /api/v1/teams/{id}/change-captain/
    Sardorni almashtirish
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            team = Team.objects.get(pk=pk)
        except Team.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if team.captain != request.user and not request.user.is_tournament_admin:
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        new_captain_id = request.data.get('player_id')
        membership = team.memberships.filter(player_id=new_captain_id, is_active=True).first()
        if not membership:
            return Response({'error': 'Bu o\'yinchi jamoada emas'}, status=status.HTTP_404_NOT_FOUND)

        # Eski sardor rolini o'zgartirish
        old_captain_membership = team.memberships.filter(player=team.captain, is_active=True).first()
        if old_captain_membership:
            old_captain_membership.role = 'player'
            old_captain_membership.save()

        # Yangi sardor
        membership.role = 'captain'
        membership.save()
        team.captain = membership.player
        team.save()

        return Response({'message': f'{membership.player.full_name} yangi sardor bo\'ldi!'})


# ============================================================
# TAKLIFLAR
# ============================================================

class TeamInvitationSendView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            team = Team.objects.get(pk=pk)
        except Team.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if team.captain != request.user and not request.user.is_tournament_admin:
            return Response({'error': 'Faqat sardor taklif yuborishishi mumkin'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TeamInviteSerializer(data=request.data)  # ← qo'shing
        serializer.is_valid(raise_exception=True)             # ← qo'shing
        player_id = serializer.validated_data['player_id']    # ← o'zgartiring

        try:
            player = User.objects.get(pk=player_id)
        except User.DoesNotExist:
            return Response({'error': 'O\'yinchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if team.memberships.filter(player=player, is_active=True).exists():
            return Response({'error': 'Bu o\'yinchi allaqachon jamoada'}, status=status.HTTP_400_BAD_REQUEST)

        existing = TeamInvitation.objects.filter(team=team, invited_player=player, status='pending').first()
        if existing:
            return Response({'error': 'Taklif allaqachon yuborilgan'}, status=status.HTTP_400_BAD_REQUEST)

        invitation = TeamInvitation.objects.create(
            team=team,
            invited_by=request.user,
            invited_player=player,
            message=serializer.validated_data.get('message', '')  # ← o'zgartiring
        )
        return Response(TeamInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


class MyInvitationsView(generics.ListAPIView):
    """
    GET /api/v1/teams/my-invitations/
    Mening takliflarim
    """
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TeamInvitation.objects.filter(
            invited_player=self.request.user,
            status='pending'
        ).select_related('team', 'invited_by')


class InvitationResponseView(APIView):
    """
    POST /api/v1/teams/invitations/{id}/respond/
    Taklifga javob berish
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invitation_id):
        try:
            invitation = TeamInvitation.objects.get(
                pk=invitation_id,
                invited_player=request.user,
                status='pending'
            )
        except TeamInvitation.DoesNotExist:
            return Response({'error': 'Taklif topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        serializer = InvitationResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        invitation.responded_at = timezone.now()

        if action == 'accept':
            invitation.status = 'accepted'
            invitation.save()
            TeamMembership.objects.create(
                team=invitation.team,
                player=request.user,
                role='player',
                jersey_number=serializer.validated_data.get('jersey_number')
            )
            return Response({'message': f'{invitation.team.name} jamoasiga qo\'shildingiz!'})
        else:
            invitation.status = 'rejected'
            invitation.save()
            return Response({'message': 'Taklif rad etildi'})


class MyTeamsView(generics.ListAPIView):
    """
    GET /api/v1/teams/my-teams/
    Mening jamoalarim
    """
    serializer_class = TeamListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        player_team_ids = TeamMembership.objects.filter(
            player=self.request.user, is_active=True
        ).values_list('team_id', flat=True)
        return Team.objects.filter(id__in=player_team_ids, is_active=True)
