# ⚽ Onside UZ — Football Tournament Management API

O'zbekiston futbol turnirlarini boshqarish uchun to'liq REST API backend.

---

## 📁 Loyiha tuzilmasi

```
onside_uz/
├── manage.py
├── requirements.txt
├── .env.example
├── onside_uz/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── apps/
    ├── accounts/       # Foydalanuvchilar, autentifikatsiya
    ├── tournaments/    # Turnirlar, guruhlar, ro'yxatga olish
    ├── teams/          # Jamoalar, a'zolik, takliflar
    ├── matches/        # O'yinlar, voqealar, statistika kiritish
    └── statistics/     # Umumiy statistika, reytinglar
```

---

## 🚀 O'rnatish va ishga tushirish

### 1. Virtual muhit yaratish
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. .env faylini sozlash
```bash
cp .env .env
# .env faylini oching va PostgreSQL ma'lumotlarini kiriting
```

### 4. PostgreSQL bazasini yaratish
```sql
CREATE DATABASE onside_uz;
CREATE USER postgres WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE onside_uz TO postgres;
```

### 5. Migratsiyalarni bajarish
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Super admin yaratish
```bash
python manage.py createsuperuser
```

### 7. Serverni ishga tushirish
```bash
python manage.py runserver
```

API: `http://localhost:8000/api/v1/`
Docs: `http://localhost:8000/api/docs/`
Admin: `http://localhost:8000/admin/`

---

## 👥 Rollar tizimi

| Rol | Imkoniyatlar |
|-----|-------------|
| `superadmin` | Hamma narsa: foydalanuvchi, turnir, admin tayinlash |
| `tournament_admin` | Turnir yaratish, o'yin boshqarish, statistika kiritish |
| `player` | Ro'yxatdan o'tish, jamoa yaratish/kirish, statistika ko'rish |

---

## 🔐 Autentifikatsiya (JWT)

Barcha so'rovlarda `Authorization` header kerak:
```
Authorization: Bearer <access_token>
```

---

## 📡 API Endpointlar

### AUTH — `/api/v1/auth/`

| Method | Endpoint | Tavsif | Ruxsat |
|--------|----------|--------|--------|
| POST | `/login/` | Login (token olish) | Hammaga |
| POST | `/register/` | Ro'yxatdan o'tish (Player) | Hammaga |
| POST | `/logout/` | Chiqish | Login |
| POST | `/token/refresh/` | Tokenni yangilash | Login |
| GET | `/me/` | Mening profilim | Login |
| PUT | `/me/` | Profilni yangilash | Login |
| POST | `/change-password/` | Parol o'zgartirish | Login |
| GET | `/players/` | Barcha o'yinchilar | Hammaga |
| GET | `/players/{id}/` | O'yinchi profili | Hammaga |
| GET | `/admin/users/` | Barcha foydalanuvchilar | Admin |
| POST | `/admin/users/` | Foydalanuvchi yaratish | Admin |
| GET | `/admin/users/{id}/` | Foydalanuvchi detail | Admin |
| PUT | `/admin/users/{id}/` | Foydalanuvchini yangilash | Admin |
| DELETE | `/admin/users/{id}/` | O'chirish (deactivate) | Admin |
| POST | `/admin/users/{id}/reset-password/` | Parol tiklash | Admin |

---

### TURNIRLAR — `/api/v1/tournaments/`

| Method | Endpoint | Tavsif | Ruxsat |
|--------|----------|--------|--------|
| GET | `/` | Barcha turnirlar | Hammaga |
| POST | `/` | Yangi turnir yaratish | Admin |
| GET | `/{id}/` | Turnir ma'lumotlari | Hammaga |
| PUT | `/{id}/` | Turnirni yangilash | Admin |
| DELETE | `/{id}/` | O'chirish | SuperAdmin |
| POST | `/{id}/status/` | Status o'zgartirish | Admin |
| GET | `/{id}/groups/` | Guruhlar ro'yxati | Hammaga |
| POST | `/{id}/groups/` | Guruh yaratish | Admin |
| GET | `/{id}/standings/` | Turnir jadvali | Hammaga |
| GET | `/{id}/registrations/` | Ro'yxatga olinganlar | Admin |
| POST | `/{id}/registrations/` | Turnirga ro'yxatdan o'tish | Captain |
| POST | `/{id}/registrations/{reg_id}/approve/` | Tasdiqlash/rad etish | Admin |

#### Turnir statuslari (ketma-ket):
```
draft → registration → ongoing → finished
```

#### Turnir formatlari:
- `league` — Liga: barcha barchaga o'ynaydi
- `knockout` — Playoff: mag'lub chiqqan keta oladi
- `group_knockout` — Guruh + Playoff aralash

---

### JAMOALAR — `/api/v1/teams/`

| Method | Endpoint | Tavsif | Ruxsat |
|--------|----------|--------|--------|
| GET | `/` | Barcha jamoalar | Hammaga |
| POST | `/` | Jamoa yaratish | Login |
| GET | `/my-teams/` | Mening jamoalarim | Login |
| GET | `/my-invitations/` | Mening takliflarim | Login |
| POST | `/invitations/{id}/respond/` | Taklifga javob | Login |
| GET | `/{id}/` | Jamoa ma'lumotlari | Hammaga |
| PUT | `/{id}/` | Yangilash | Captain/Admin |
| DELETE | `/{id}/` | O'chirish | Captain/Admin |
| GET | `/{id}/members/` | A'zolar ro'yxati | Hammaga |
| POST | `/{id}/members/` | A'zo qo'shish | Captain/Admin |
| DELETE | `/{id}/members/{player_id}/` | A'zoni chiqarish | Captain/Admin |
| POST | `/{id}/change-captain/` | Sardorni almashtirish | Captain/Admin |
| POST | `/{id}/invite/` | Taklif yuborish | Captain |

---

### O'YINLAR — `/api/v1/matches/`

| Method | Endpoint | Tavsif | Ruxsat |
|--------|----------|--------|--------|
| GET | `/` | Barcha o'yinlar | Hammaga |
| POST | `/` | O'yin yaratish | Admin |
| GET | `/{id}/` | O'yin detail | Hammaga |
| PUT | `/{id}/` | O'yinni yangilash | Admin |
| DELETE | `/{id}/` | O'chirish | Admin |
| POST | `/{id}/score/` | Hisobni yangilash | MatchAdmin |
| POST | `/{id}/status/` | Status o'zgartirish | MatchAdmin |
| GET | `/{id}/events/` | Voqealar (gol, assist...) | Hammaga |
| POST | `/{id}/events/` | Voqea qo'shish | MatchAdmin |
| DELETE | `/{id}/events/{event_id}/` | Voqeani o'chirish | MatchAdmin |
| GET | `/{id}/stats/` | O'yinchi statistikalari | Hammaga |
| POST | `/{id}/stats/add/` | Statistika kiritish | MatchAdmin |
| POST | `/{id}/stats/bulk/` | Ko'plab statistika kiritish | MatchAdmin |

#### O'yin voqea turlari:
| Tur | Kod |
|-----|-----|
| Gol | `goal` |
| Assist | `assist` |
| O'z darvozasiga | `own_goal` |
| Sariq karta | `yellow_card` |
| Qizil karta | `red_card` |
| Almashtirildi (kirdi) | `substitution_in` |
| Almashtirildi (chiqdi) | `substitution_out` |

---

### STATISTIKA — `/api/v1/statistics/`

| Method | Endpoint | Tavsif | Ruxsat |
|--------|----------|--------|--------|
| GET | `/players/{id}/` | O'yinchi statistikasi | Hammaga |
| GET | `/my-stats/` | Mening statistikam | Login |
| GET | `/top-scorers/` | Eng ko'p gol urganlar | Hammaga |
| GET | `/top-assists/` | Eng ko'p assist berganlar | Hammaga |
| GET | `/leaderboard/` | Umumiy reyting | Hammaga |
| GET | `/teams/` | Jamoalar statistikasi | Hammaga |
| GET | `/tournament/{id}/summary/` | Turnir xulosasi | Hammaga |

#### Query parametrlar:
```
?tournament_id=1    — Turnir bo'yicha filter
?limit=10           — Natijalar soni (max 50)
```

---

## 📦 So'rov namunalari

### Login
```bash
POST /api/v1/auth/login/
{
  "username": "admin",
  "password": "password123"
}
```

### Turnir yaratish
```bash
POST /api/v1/tournaments/
Authorization: Bearer <token>
{
  "name": "Toshkent Kubogi 2025",
  "format": "league",
  "max_teams": 8,
  "start_date": "2025-06-01",
  "end_date": "2025-07-01",
  "location": "Toshkent"
}
```

### O'yin statusi live ga o'tkazish
```bash
POST /api/v1/matches/1/status/
Authorization: Bearer <token>
{
  "status": "live"
}
```

### Gol kiritish (voqea orqali)
```bash
POST /api/v1/matches/1/events/
Authorization: Bearer <token>
{
  "player": 5,
  "team": 2,
  "event_type": "goal",
  "minute": 34,
  "description": "Burchak zarbasidan so'ng"
}
```

### Ko'plab statistika kiritish
```bash
POST /api/v1/matches/1/stats/bulk/
Authorization: Bearer <token>
{
  "stats": [
    {"player_id": 5, "team": 2, "goals": 2, "assists": 1, "minutes_played": 90},
    {"player_id": 7, "team": 2, "goals": 0, "assists": 2, "minutes_played": 90},
    {"player_id": 9, "team": 3, "goals": 1, "assists": 0, "minutes_played": 75}
  ]
}
```

### Jamoaga a'zo taklif qilish
```bash
POST /api/v1/teams/1/invite/
Authorization: Bearer <token>
{
  "player_id": 12,
  "message": "Bizning jamoaga qo'shiling!"
}
```

### Turnir jadvali
```bash
GET /api/v1/tournaments/1/standings/
```

---

## ⚙️ Admin Panel

`/admin/` — Django admin paneli orqali barcha ma'lumotlarni to'g'ridan boshqarish mumkin.

---

## 📄 API Dokumentatsiya

Server ishga tushgandan so'ng:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **OpenAPI schema**: `http://localhost:8000/api/schema/`
