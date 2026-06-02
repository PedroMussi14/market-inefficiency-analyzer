FROM python:3.11-slim

# Install system dependencies for Playwright (without relying on playwright install --with-deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget gnupg ca-certificates fonts-liberation fonts-unifont libnss3 libxss1 libasound2 \
        libatk-bridge2.0-0 libdrm2 libgbm1 libgtk-3-0 libxcomposite1 libxdamage1 \
        libxfixes3 libxrandr2 libxkbcommon0 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
        libatspi2.0-0 libatk1.0-0 libglib2.0-0 libdbus-1-3 libx11-6 libx11-xcb1 libxcb1 \
        libxdmcp6 libxau6 libxext6 libxrender1 libxinerama1 libxrandr2 libxcursor1 libxi6 \
        libgdk-pixbuf-2.0-0 libpango-1.0-0 libcairo2 libxcomposite1 libxdamage1 libfribidi0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install --with-deps chromium || python -m playwright install chromium

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000
