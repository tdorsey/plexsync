from __future__ import absolute_import, unicode_literals
from celery import Celery

celery = Celery('plexsync',
             broker='pyamqp://rabbitmq:rabbitmq@rabbitmq//',
             backend='redis://redis:6379/0',
             include=['plexsync.plexsync'])

# Optional configuration, see the application user guide.
celery.conf.update(
    result_expires=3600,
)

def getCelery(self):
    return celery or Celery('plexsync',
             broker='pyamqp://rabbitmq:rabbitmq@rabbitmq//',
             backend='redis://redis:6379/0',
             include=['plexsync.plexsync'])

if __name__ == '__main__':
    celery.start(argv=['celery', 'worker', '-l', 'debug'])
