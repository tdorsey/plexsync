import logging, time

from flask import url_for as _url_for, current_app, _request_ctx_stack

logger = logging.getLogger(__name__)

def timing(func):
    def wrap(f):
        start_time = time.time()
        ret = func(f)
        end_time = time.time()
        elapsed = end_time - start_time
        logger.debug(f"{ret.__name__} took {elapsed.microseconds * 1000} ms")
        return ret
    return wrap


def timestamp():
    """Return the current timestamp as an integer."""
    return int(time.time())


def url_for(*args, **kwargs):
    """
    url_for replacement that works even when there is no request context.
    """
    if '_external' not in kwargs:
        kwargs['_external'] = False
    reqctx = _request_ctx_stack.top
    if reqctx is None:
        if kwargs['_external']:
            raise RuntimeError('Cannot generate external URLs without a '
                               'request context.')
        with current_app.test_request_context():
            return _url_for(*args, **kwargs)
    return _url_for(*args, **kwargs)
