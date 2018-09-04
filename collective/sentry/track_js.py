import Globals
import logging
import os
from collective.sentry.browser.interfaces import IUserInfo
from collective.sentry.config import ALLOWED_JS
from collective.sentry.config import IGNORED_JS
from collective.sentry.config import IGNORED_JS_ERRORS
from collective.sentry.config import DSN_ENV_VAR
from collective.sentry.config import ENVIRONMENT_ENV_VAR
from collective.sentry.config import RELEASE_ENV_VAR
from collective.sentry.config import SEND_ANYWAY_ENV_VAR
from collective.sentry.config import TRACK_JS_ENV_VAR
from Products.Five import BrowserView
from zope.component import getMultiAdapter


logger = logging.getLogger('collective.sentry')


SENTRY_INIT = """Raven.config('%s', {
    whiteListUrls: [%s],
    ignoreErrors: [%s],
    ignoreUrls: [%s],
    environment: '%s',
    release: '%s'
}).install();
Raven.setUserContext(%s);
console.log('raven installed');
"""


class SentryConfig(BrowserView):
    """ Config js for Sentry
    """

    def __call__(self):
        result = ""
        dsn = ""
        error_log = self.context.get('error_log', None)
        allowed_urls = os.environ.get(ALLOWED_JS, '')
        ignore_urls = os.environ.get(IGNORED_JS, '')
        ignore_errors = os.environ.get(IGNORED_JS_ERRORS, '')
        environment = os.environ.get(ENVIRONMENT_ENV_VAR, '')
        release = os.environ.get(RELEASE_ENV_VAR, '')
        ignore_errors = os.environ.get(IGNORED_JS_ERRORS, '')
        if error_log:
            props = error_log.getProperties()
            dsn = props.get('getsentry_dsn', "")
            track = props.get('track_js', False)
            if not track:
                track = bool(os.environ.get(TRACK_JS_ENV_VAR, False))
            send_anyway = os.environ.get(SEND_ANYWAY_ENV_VAR, '')
            if track and Globals.DevelopmentMode and not send_anyway:
                track = False
                logger.info(
                    'Zope is in debug mode. Not sending JS errors to sentry')
        dsn = dsn and dsn or os.environ.get(DSN_ENV_VAR, '')
        if dsn and track:
            adapter = getMultiAdapter((self.context, self.request), IUserInfo)
            user_data = str(adapter.get_user_data())
            result = SENTRY_INIT % (dsn,
                                    allowed_urls,
                                    ignore_errors,
                                    ignore_urls,
                                    environment,
                                    release,
                                    user_data)
        elif dsn and not track:
            logger.info(
                'JS tracking not enabled. Not sending JS errors to sentry')
        else:
            logger.info("There is no GetSentry DSN set. Not "
                        "configuring Sentry for JS")

        self.request.response.setHeader('Content-Type',
                                        'application/javascript')

        return result
