from collective.sentry.config import CA_CERTS_ENV_VAR
from collective.sentry.config import ENVIRONMENT_ENV_VAR
from collective.sentry.config import RELEASE_ENV_VAR
import logging
import os
import sentry_sdk

logger = logging.getLogger(__name__)

environment = os.environ.get(ENVIRONMENT_ENV_VAR, None)
release = os.environ.get(RELEASE_ENV_VAR, '')
ca_certs = os.environ.get(CA_CERTS_ENV_VAR, None)


def extra_config(startup):
    """Called by ``pprocrastinate worker`` with the Zope starter, before jobs run.

    Failed jobs bypass the error_log; collective.procrastinate logs them at
    ERROR, which sentry_sdk's default logging integration reports.
    """
    env = getattr(startup.cfg, 'environment', None)
    if env and 'GETSENTRY_DSN' in env:
        sentry_sdk.init(
            dsn=env['GETSENTRY_DSN'],
            environment=environment,
            release=release,
            ca_certs=ca_certs,
        )
        logger.warning("Initialized Sentry for the job worker.")
