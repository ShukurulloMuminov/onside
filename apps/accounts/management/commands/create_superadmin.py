"""
python manage.py create_superadmin
Dastlabki super admin yaratish uchun
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Dastlabki Onside UZ super admin yaratish'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin')
        parser.add_argument('--password', type=str, default='Admin@12345')
        parser.add_argument('--email', type=str, default='admin@onside.uz')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'"{username}" allaqachon mavjud'))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=User.Role.SUPERADMIN,
            first_name='Onside',
            last_name='Admin'
        )
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Super Admin yaratildi!\n'
            f'   Username : {username}\n'
            f'   Password : {password}\n'
            f'   Email    : {email}\n'
            f'   Rol      : Super Admin\n\n'
            f'⚠️  Parolni o\'zgartiring!\n'
        ))
