from celery.utils.log import get_task_logger
from collective.sentry.config import CA_CERTS_ENV_VAR
from collective.sentry.config import ENVIRONMENT_ENV_VAR
from collective.sentry.config import RELEASE_ENV_VAR
from sentry_sdk.integrations.celery import CeleryIntegration
import sentry_sdk
import os

logger = get_task_logger(__name__)

environment = os.environ.get(ENVIRONMENT_ENV_VAR, None)
release = os.environ.get(RELEASE_ENV_VAR, '')
ca_certs = os.environ.get(CA_CERTS_ENV_VAR, None)


def extra_config(startup):
    env = getattr(startup.cfg, 'environment', None)
    if env and 'GETSENTRY_DSN' in env:
        sentry_sdk.init(
            dsn=env['GETSENTRY_DSN'],
            integrations=[CeleryIntegration()],
            environment=environment,
            release=release,
            ca_certs=ca_certs,
        )
        logger.warn("Initialized Sentry with celery integration.")
