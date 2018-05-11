#!/bin/sh
python3 /app/app.py
celery worker --app=plexsync -l error -Ofair
