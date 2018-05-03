from __future__ import absolute_import, unicode_literals
from celery import Celery

celery = Celery('plexsync',
             broker='pyamqp://guest@localhost//',
             result_backend='redis://localhost:6379/0',
             include=['plexsync.plexsync'])

# Optional configuration, see the application user guide.
celery.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    celery.start()

