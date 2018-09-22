#!/bin/sh
#celery multi start worker1 -A plexsync \
#xloglevel=DEBUG

#celery worker -A plexsync -l debug -Ofair 
celery -A plexsync.tasks worker --detach --concurrency=1 -l info -Ofair --uid plexsync --pidfile="%n.pid"   --logfile="%n%I.log" \
 && python3 /app/app.py  

