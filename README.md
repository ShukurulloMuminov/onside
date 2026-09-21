# OnSide.uz

Havaskor futbolchilar uchun raqamli futbol platformasi — futbolchi → jamoa → turnir → o'yin →
statistika → reyting.

## Arxitektura

- `backend/` — Django + Django REST Framework API (`/api/v1/...`), JWT auth, PostgreSQL.
- `frontend/` — Next.js (App Router) frontend, BFF pattern (httpOnly cookies, JWT never reaches the browser).
- `docker-compose.yml` — local PostgreSQL for the backend (host port `5434`).

Full architecture rationale — apps, permission model, tournament/stats engine, MVP roadmap — is in the plan this was built from.

## Ishga tushirish (local dev)

### 1. Postgres

```bash
docker compose up -d
```

### 2. Backend

Run from the repo root (`~/onside`) — each step below assumes you `cd` there first, not from
inside another step's directory:

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # already points at the docker-compose Postgres on :5434
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data       # optional: 4-team group+playoff tournament
python manage.py seed_big_tournament  # optional: full 16-team knockout bracket (R16 -> QF -> SF -> Final + 3rd place)
python manage.py runserver 8010
```

- API: http://127.0.0.1:8010/api/v1/
- API docs (Swagger): http://127.0.0.1:8010/api/docs/
- Django admin: http://127.0.0.1:8010/admin/
- Tests: `pytest`

Demo logins after `seed_demo_data` (password `Demo12345!` for all): `tournament_admin`,
`ali_karimov`, `vali_toshev`, `otabek_yoldoshev`, ... (see `core/management/commands/seed_demo_data.py`).
`seed_big_tournament` seeds its own 16 teams (usernames `sl_*`, same password) — mainly useful
for exercising/demoing the full bracket view rather than for logging in as a specific player.

### 3. Frontend

In a **new terminal**, back at the repo root (`~/onside`) — not inside `backend/`:

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:3000
- `.env.local` points `DJANGO_API_URL` at the backend (defaults to `http://127.0.0.1:8010/api/v1`).

## Sign in with Google (optional)

The login/register pages show a Google button automatically once it's configured — no code
changes needed:

1. In [Google Cloud Console](https://console.cloud.google.com/apis/credentials), create an
   **OAuth client ID** → Application type **Web application**.
2. Add `http://localhost:3000` under **Authorized JavaScript origins** (add your production
   domain too when you deploy).
3. Copy the client ID into **both**:
   - `backend/.env` → `GOOGLE_CLIENT_ID=...`
   - `frontend/.env.local` → `NEXT_PUBLIC_GOOGLE_CLIENT_ID=...`
4. Restart both dev servers.

New Google sign-ins auto-create a player account (empty profile, no password) matched by
verified email; if that email already has a password account, Google sign-in logs into the same
account instead of creating a duplicate.

## MVP scope

This build covers **MVP1**: auth (incl. Google sign-in), player profiles, teams (multi-team
membership, invite by Player ID, configurable 5x5/7x7/11x11 squad size with a starting-lineup
pitch graphic), tournaments (registration, group stage, round-robin fixtures, standings, knockout
bracket with auto-advance and connector-line bracket view), match events, live-computed stats,
and rankings.

**MVP2 in progress**: Badges & Levels are done (see below). Notifications, fields, sponsors, ads,
and match confirmation are not yet built. Telegram bot, mobile app, and geolocation are **MVP3**
— the API is versioned and service-layer-based specifically so those can be added without
reworking the core.

### Badges & Levels

- **Level** — a player's career tier (Rookie → ... → Legend, 10 defaults) is *computed*, not
  stored: `gamification.services.get_level_for_player()` scores a player's cached stats
  (goals/assists/wins/MVP/matches) against `Level.required_points` thresholds. Super Admin can
  rename/re-tier levels via Django admin (`/admin/gamification/level/`) or `PATCH
  /api/v1/levels/{id}/`.
- **Badge** — Super Admin manually awards badges (Tournament Winner, MVP, Top Scorer, ...) to a
  player by Player ID: `POST /api/v1/badges/{id}/award/` with `{"player_id": "1024"}` (also
  reachable from the Super Admin panel on `/dashboard`). `is_automatic` is reserved for a future
  criteria-based auto-award engine — MVP2 only supports manual awarding.
- Both show on every public player profile automatically once set.
