FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# libpq-dev + gcc for psycopg2-binary's build deps on some base images;
# harmless if the wheel is used instead.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

# migrate + collectstatic run here, at container startup, once real
# SECRET_KEY/DATABASE_URL env vars are available — not at build time.
ENTRYPOINT ["./docker-entrypoint.sh"]
