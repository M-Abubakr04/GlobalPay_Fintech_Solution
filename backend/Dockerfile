FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
RUN groupadd --system globalpay \
    && useradd --system --gid globalpay --home-dir /app globalpay \
    && chmod +x /app/entrypoint.sh \
    && chown -R globalpay:globalpay /app

EXPOSE 8000
USER globalpay
ENTRYPOINT ["/app/entrypoint.sh"]
