import functools
import logging
import six
import os
import threading
from AccessControl.class_init import InitializeClass
from AccessControl import ClassSecurityInfo
from App.config import getConfiguration
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog
from Products.SiteErrorLog.SiteErrorLog import use_error_logging
from datetime import datetime
from datetime import timedelta
from collective.sentry.config import SEND_ANYWAY_ENV_VAR
from collective.sentry.config import DSN_ENV_VAR
from collective.sentry.config import ENVIRONMENT_ENV_VAR
from collective.sentry.config import RELEASE_ENV_VAR
from collective.sentry.config import TRACK_JS_ENV_VAR
from collective.sentry.config import USER_FEEDBACK_ENV_VAR
from inspect import currentframe
from inspect import getinnerframes
from inspect import getouterframes
from logging import ERROR
from logging import LogRecord
from raven.handlers.logging import SentryHandler
from raven.utils.stacks import iter_stack_frames


logger = logging.getLogger('collective.sentry')

EXC = {}
TIMEOUT = timedelta(minutes=3)

_www = os.path.dirname(__file__)

handler_store = threading.local()

handler_store.handlers = dict()


def get_or_create_handler(dsn):
    if not hasattr(handler_store, 'handlers'):
        handler_store.handlers = dict()
        logger.info('Creating new handlers.')
    if not dsn.startswith('threaded+'):
        dsn = 'threaded+' + dsn
    if dsn not in handler_store.handlers:
        environment = os.environ.get(ENVIRONMENT_ENV_VAR, '')
        release = os.environ.get(RELEASE_ENV_VAR, '')
        handler_store.handlers[dsn] = ZopeSentryHandler(
            dsn=dsn,
            environment=environment,
            release=release)
        logger.info('Creating new handler for DSN: %s' % dsn)
    return handler_store.handlers[dsn]


class GetSentryErrorLog(SiteErrorLog):
    """ Site error log that sends errors to getsentry """

    meta_type = 'GetSentry Error Log'

    getsentry_dsn = ''
    track_js = False

    _ignored_exceptions = SiteErrorLog._ignored_exceptions + ('Intercepted',
        'CheckoutException', 'LinkIntegrityNotificationException')

    security = ClassSecurityInfo()

    security.declareProtected(use_error_logging, 'manage_main')
    manage_main = PageTemplateFile('main.pt', _www)

    security.declarePrivate('raising')
    def raising(self, info):
        """ Log an exception and send the info to getsentry """
        res = SiteErrorLog.raising(self, info)
        send_anyway = os.environ.get(SEND_ANYWAY_ENV_VAR, '')
        if getConfiguration().debug_mode and not send_anyway:
            # We are in debug mode, do not send tb to Sentry
            logger.info('Zope is in debug mode. Not sending error to sentry')
            return res

        dsn = self.getsentry_dsn
        dsn = dsn and dsn or os.environ.get(DSN_ENV_VAR, '')
        if not dsn:
            logger.warn('Missing DSN. Unable to send errors to getsentry')
            return res

        if res is not None:

            try:
                tp = str(getattr(info[0], '__name__', info[0]))
            except Exception:
                return res

            now = datetime.now()
            # Clean out EXC dict of old entries
            for k in EXC.keys():
                if (now - EXC[k]) > TIMEOUT:
                    del EXC[k]
            key = '%s:%s' % ('/'.join(self.getPhysicalPath()),tp)
            if key in EXC:
                # We just cleaned out old entries so if key is still in there
                # it is ok to just return without checking against TIMEOUT
                return res

            EXC[key] = now
            rec = LogRecord('exception', ERROR, '', 1, 'Exception', (), info)
            handler = get_or_create_handler(dsn)
            handler.emit(rec)

        return res

    security.declareProtected(use_error_logging, 'getProperties')
    def getProperties(self):
        props = SiteErrorLog.getProperties(self)
        props['getsentry_dsn'] = self.getsentry_dsn
        props['env_dsn'] = os.environ.get(DSN_ENV_VAR, '')
        props['track_js'] = self.track_js
        return props

    security.declareProtected(use_error_logging, 'setProperties')
    def setProperties(self, keep_entries, copy_to_zlog=0,
                      ignored_exceptions=(), getsentry_dsn='',
                      track_js=0, RESPONSE=None):
        """Sets the properties of this site error log.
        """

        getsentry_dsn = getsentry_dsn.strip()
        if getsentry_dsn != self.getsentry_dsn:
            self.getsentry_dsn = getsentry_dsn

        self.track_js = bool(track_js)
        exceptions = list()
        for entry in ignored_exceptions:
            if entry:
                value = entry
                if not isinstance(value, six.text_type):
                    value = value.decode('utf-8')
                exceptions.append(value)

        SiteErrorLog.setProperties(self, keep_entries, copy_to_zlog,
                                   exceptions, RESPONSE)

InitializeClass(GetSentryErrorLog)

def manage_addErrorLog(dispatcher, RESPONSE=None):
    """Add a site error log to a container."""
    log = GetSentryErrorLog()
    dispatcher._setObject(log.id, log)
    if RESPONSE is not None:
        RESPONSE.redirect(
            dispatcher.DestinationURL() +
            '/manage_main?manage_tabs_message=GetSentry+Error+Log+Added.' )



class ZopeSentryHandler(SentryHandler):
    '''
    Zope unfortunately eats the stack trace information.
    To get the stack trace information and other useful information
    from the request object, this class looks into the different stack
    frames when the emit method is invoked.
    '''

    def __init__(self, *args, **kw):
        kw['capture_locals'] = False
        super(ZopeSentryHandler, self).__init__(*args, **kw)
        level = kw.get('level', logging.ERROR)
        self.setLevel(level)

    def emit(self, record):
        request = None
        if record.levelno <= logging.ERROR:
            exc_info = None
            for frame_info in getouterframes(currentframe()):
                frame = frame_info[0]
                if not request:
                    request = frame.f_locals.get('request', None)
                    if not request:
                        view = frame.f_locals.get('self', None)
                        request = getattr(view, 'request', None)
                if not exc_info:
                    exc_info = frame.f_locals.get('exc_info', None)
                    if not hasattr(exc_info, '__getitem__'):
                        exc_info = None
                if request and exc_info:
                    break

            if exc_info:
                record.exc_info = exc_info
                record.stack = \
                    iter_stack_frames(getinnerframes(exc_info[2]))
            if request:
                try:
                    body_pos = request.stdin.tell()
                    # request.stdin.seek(0)
                    # body = request.stdin.read()
                    # request.stdin.seek(body_pos)
                    http = dict(headers=request.environ,
                                url=request.getURL(),
                                method=request.method,
                                host=request.environ.get('REMOTE_ADDR',''),
                                )
                                # data=body)
                    if 'HTTP_USER_AGENT' in http['headers']:
                        if 'User-Agent' not in http['headers']:
                            http['headers']['User-Agent'] = \
                                http['headers']['HTTP_USER_AGENT']
                    if 'QUERY_STRING' in http['headers']:
                        http['query_string'] = http['headers'
                                ]['QUERY_STRING']
                    setattr(record, 'sentry.interfaces.Http', http)
                    user = request.get('AUTHENTICATED_USER', None)
                    if user is not None:
                        user_dict = dict(id=user.getId(),
                                is_authenticated=user.has_role('Authenticated'
                                ), email=user.getProperty('email'))
                    else:
                        user_dict = dict(id='Anonymous User',
                                is_authenticated=False,
                                email='')
                    setattr(record, 'sentry.interfaces.User', user_dict)
                except (AttributeError, KeyError):
                    logger.warning('Could not extract data from request',
                            exc_info=True)
        emitted = super(ZopeSentryHandler, self).emit(record)
        track_js = os.environ.get(TRACK_JS_ENV_VAR, 'false')
        user_feedback = os.environ.get(USER_FEEDBACK_ENV_VAR, 'false')
        if request and track_js != 'false' and user_feedback != 'false':
            request.other['SENTRY_ID'] = emitted
            request.other['SENTRY_DSN'] = self.client.get_public_dsn(scheme='https')
        return emitted


def captureMessage(message, **kwargs):
    dsn = os.environ.get(DSN_ENV_VAR, '')
    if dsn:
        handler = get_or_create_handler(dsn)
        handler.client.captureMessage(message, **kwargs)


def captureBreadcrumb(**kwargs):
    dsn = os.environ.get(DSN_ENV_VAR, '')
    if dsn:
        handler = get_or_create_handler(dsn)
        handler.client.captureBreadcrumb(**kwargs)


def breadcrumb(message, category, level='info', include_result=False):

    def decorator_breadcrumb(func):

        @functools.wraps(func)
        def wrapper_breadcrumb(*args, **kwargs):
            value = func(*args, **kwargs)
            dsn = os.environ.get(DSN_ENV_VAR, '')
            if dsn:
                data = {'args': args, 'kwargs': kwargs}
                if include_result:
                    data['result'] = value
                handler = get_or_create_handler(dsn)
                handler.client.captureBreadcrumb(
                    message=message,
                    category=category,
                    level=level,
                    data=data)
            return value

        return wrapper_breadcrumb
    return decorator_breadcrumb
