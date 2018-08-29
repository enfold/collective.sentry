from celery.utils.log import get_task_logger
from raven import Client
from raven.contrib.celery import register_signal
from raven.contrib.celery import register_logger_signal


logger = get_task_logger(__name__)


def extra_config(startup):
    env = getattr(startup.cfg, 'environment', None)
    if env and 'GETSENTRY_DSN' in env:
        client = Client(env['GETSENTRY_DSN'])
        register_logger_signal(client)
        register_signal(client)
        logger.warn("Registered Sentry client with collective.celery.")
