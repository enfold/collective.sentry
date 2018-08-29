import Globals
import logging
import os
from collective.sentry.config import ADDITIONAL_JS_TO_IGNORE
from collective.sentry.config import DSN_ENV_VAR
from collective.sentry.config import SEND_ANYWAY_ENV_VAR
from collective.sentry.config import TRACK_JS_ENV_VAR
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView


logger = logging.getLogger('collective.sentry')


SENTRY_INIT = """import { init } from '@sentry/browser';

init({
  dsn: '%s'
});
console.log("Initialized sentry JS")
"""


class SentryConfig(BrowserView):
    """ Config js for Sentry
    """

    def __call__(self):
        result = ""
        dsn = ""
        error_log = self.context.get('error_log', None)
        if error_log:
            props = error_log.getProperties()
            dsn = props.get('getsentry_dsn', "")
            dsn = dsn and dsn or os.environ.get(DSN_ENV_VAR, '')
        if dsn:
            result = SENTRY_INIT % dsn
        else:
            logger.info("There is no GetSentry DSN set. Not "
                        "configuring Sentry for JS")

        self.request.response.setHeader('Content-Type',
                                        'application/javascript')

        return result


class Control(BrowserView):
    """ JS tracking control
    """

    def should_track_js(self):
        track = False
        error_log = getToolByName(self.context, 'error_log', None)
        if error_log:
            props = error_log.getProperties()
            track = props.get('track_js', False)
            if not track:
                track = bool(os.environ.get(TRACK_JS_ENV_VAR, False))

            send_anyway = os.environ.get(SEND_ANYWAY_ENV_VAR, '')
            if track and Globals.DevelopmentMode and not send_anyway:
                # We are in debug mode, do not send tb to Sentry
                logger.info(
                    'Zope is in debug mode. Not sending JS errors to sentry')
                track = False

        return track

    def additional_js_to_ignore(self):
        to_ignore = os.environ.get(ADDITIONAL_JS_TO_IGNORE, '')
        for s in to_ignore.split(';'):
            if s and s in self.request.URL:
                logger.debug(
                    ('"%s" is part of the URL %s. Ignoring from JS monitoring.'
                     % (s, self.request.URL))
                )
                return True
        return False
