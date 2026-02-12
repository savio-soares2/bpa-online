FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend_django /app/backend_django
COPY backend /app/backend

WORKDIR /app/backend_django

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
