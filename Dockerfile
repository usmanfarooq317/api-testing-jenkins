# Dockerfile - lightweight single-file Flask app
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# copy files
COPY app.py /app/app.py
COPY requirements.txt /app/requirements.txt

# install deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get purge -y --auto-remove build-essential \
 && rm -rf /var/lib/apt/lists/*

EXPOSE 5090

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5090", "--workers", "2", "--timeout", "120"]
