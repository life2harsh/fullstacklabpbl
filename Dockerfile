FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads/avatars uploads/posts uploads/messages

RUN python manage.py collectstatic --noinput

CMD ["sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 8000 vortex.asgi:application"]
