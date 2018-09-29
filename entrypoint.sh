#!/bin/sh

#celery worker -A plexsync -l debug -Ofair 
celery -A plexsync_flask --detach --concurrency=1 -l debug -Ofair --uid plexsync --pidfile="%n.pid"   --logfile="%n%I.log" 
# && #python3 /app/plexsync_flask  

