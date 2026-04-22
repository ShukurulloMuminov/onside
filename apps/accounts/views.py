from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegisterSerializer,
    AdminCreateUserSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    UserListSerializer,
)
from .permissions import IsSuperAdmin, IsTournamentAdmin, IsOwnerOrAdmin


class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Login - JWT access va refresh token qaytaradi
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Oddiy ro'yxatdan o'tish - faqat PLAYER roli
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Ro\'yxatdan o\'tish muvaffaqiyatli!',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Logout - refresh tokenni blacklistga qo'shadi
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Chiqish muvaffaqiyatli!'})
        except Exception:
            return Response({'error': 'Noto\'g\'ri token'}, status=status.HTTP_400_BAD_REQUEST)


class MyProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/auth/me/   - Mening profilim
    PUT  /api/v1/auth/me/   - Profilni yangilash
    PATCH /api/v1/auth/me/  - Qisman yangilash
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/
    Parolni o'zgartirish
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Eski parol noto\'g\'ri'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Parol muvaffaqiyatli o\'zgartirildi!'})


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

class AdminUserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/auth/admin/users/       - Barcha foydalanuvchilar
    POST /api/v1/auth/admin/users/       - Yangi foydalanuvchi yaratish (admin)
    Admin foydalanuvchi yaratadi, rol va parol beradi
    """
    permission_classes = [IsTournamentAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['role', 'is_active', 'position']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminCreateUserSerializer
        return UserListSerializer

    def get_queryset(self):
        return User.objects.all().order_by('-created_at')

    def create(self, request, *args, **kwargs):
        # Faqat superadmin tournament_admin yarata oladi
        if request.data.get('role') == 'tournament_admin' and not request.user.is_superadmin:
            return Response(
                {'error': 'Turnir admin yaratish uchun Super Admin huquqi kerak'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/auth/admin/users/{id}/  - Foydalanuvchi ma'lumotlari
    PUT    /api/v1/auth/admin/users/{id}/  - Yangilash
    DELETE /api/v1/auth/admin/users/{id}/  - O'chirish
    """
    permission_classes = [IsTournamentAdmin]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AdminCreateUserSerializer
        return UserProfileSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            return Response({'error': 'O\'zingizni o\'chira olmaysiz'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = False
        user.save()
        return Response({'message': f'{user.username} o\'chirildi (deactivated)'})


class AdminResetPasswordView(APIView):
    """
    POST /api/v1/auth/admin/users/{id}/reset-password/
    Admin foydalanuvchi parolini tiklaydi
    """
    permission_classes = [IsTournamentAdmin]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Foydalanuvchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        new_password = request.data.get('new_password')
        if not new_password:
            return Response({'error': 'new_password majburiy'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': f'{user.username} paroli yangilandi!'})


class PublicPlayerListView(generics.ListAPIView):
    """
    GET /api/v1/auth/players/
    Barcha o'yinchilar ro'yxati (public)
    """
    serializer_class = UserListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['username', 'first_name', 'last_name']

    def get_queryset(self):
        return User.objects.filter(role='player', is_active=True)


class PublicPlayerDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/auth/players/{id}/
    O'yinchi profili (public)
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.filter(role='player', is_active=True)
