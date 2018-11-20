#!/bin/bash

celery worker -Ofair -A plexsync_flask &
nohup  flask run plexsync_flask --host 0.0.0.0
