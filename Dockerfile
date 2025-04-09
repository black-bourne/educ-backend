# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Environment variables to avoid writing .pyc files and buffer stdout/stderr.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Run Gunicorn with Gunicorn settings.
CMD ["gunicorn", "educ_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

