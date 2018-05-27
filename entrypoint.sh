#!/bin/sh

celery worker --detach --workdir=/app --app=plexsync -l info -Ofair --uid plexsync 
python3 /app/app.py  

