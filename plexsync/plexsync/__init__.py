import logging
from .plexsync import PlexSync
log = logging.getLogger("plexsync")


# Logging Configuration
#log = logging.getLogger('plexsync')
#logfile = CONFIG.get('log.path')
#logformat = CONFIG.get('log.format', '%(asctime)s %(module)12s:%(lineno)-4s %(levelname)-9s %(message)s')
loglevel = logging.DEBUG
loghandler = logging.NullHandler()

#if logfile:  # pragma: no cover
#    logbackups = CONFIG.get('log.backup_count', 3, int)
#    logbytes = CONFIG.get('log.rotate_bytes', 512000, int)
#    loghandler = RotatingFileHandler(os.path.expanduser(logfile), 'a', logbytes, logbackups)

#loghandler.setFormatter(logging.Formatter(logformat))
log.addHandler(loghandler)
log.setLevel(loglevel)
#logfilter = SecretsFilter()
#if CONFIG.get('log.show_secrets', '').lower() != 'true':
#    log.addFilter(logfilter)


log.debug(f"Initializing PlexSync module")
log.info(f"Initializing PlexSync module")
log.warning(f"Initializing PlexSync module")
log.error(f"Initializing PlexSync module")
log.critical(f"Initializing PlexSync module")
