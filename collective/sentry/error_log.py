import functools
import logging
import six
import os
from AccessControl.class_init import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.users import nobody
from AccessControl.SecurityManagement import getSecurityManager
from App.config import getConfiguration
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog
from Products.SiteErrorLog.SiteErrorLog import use_error_logging
from collective.sentry.config import SEND_ANYWAY_ENV_VAR
from collective.sentry.config import DSN_ENV_VAR
from collective.sentry.config import ENVIRONMENT_ENV_VAR
from collective.sentry.config import RELEASE_ENV_VAR
from collective.sentry.config import TRACK_JS_ENV_VAR
from collective.sentry.config import USER_FEEDBACK_ENV_VAR
from sentry_sdk.hub import Hub
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.utils import event_from_exception
from zope.globalrequest import getRequest
from ZPublisher.HTTPRequest import _filterPasswordFields
from plone import api
import sentry_sdk
import sys


logger = logging.getLogger('collective.sentry')

_www = os.path.dirname(__file__)


def get_or_create_client(dsn):
    if Hub.current.client:
        if Hub.current.client.dsn == dsn:
            return Hub.current.client

    environment = os.environ.get(ENVIRONMENT_ENV_VAR, None)
    release = os.environ.get(RELEASE_ENV_VAR, '')
    client = sentry_sdk.client.Client(
        dsn,
        max_breadcrumbs=50,
        debug=False,
        environment=environment,
        release=release,
        integrations=[LoggingIntegration(
            level=None,
            event_level=None
        )])
    Hub.current.bind_client(client)
    return client


def _get_user_from_request(request):
    user = request.get("AUTHENTICATED_USER", None)

    if user is None:
        user = getSecurityManager().getUser()

    if user is not None and user != nobody:
        user_dict = {
            "id": user.getId(),
            "email": user.getProperty("email") or "",
        }
    else:
        user_dict = {}

    return user_dict


def _get_other_from_request(request):
    other = dict()
    for k, v in _filterPasswordFields(request.other.items()):
        if k in ("PARENTS", "RESPONSE"):
            continue
        other[k] = repr(v)
    return other


def _get_lazyitems_from_request(request):
    lazy_items = dict()
    for k, v in _filterPasswordFields(request._lazies.items()):
        lazy_items[k] = repr(v)
    return lazy_items


def _get_cookies_from_request(request):
    cookies = dict()
    for k, v in _filterPasswordFields(request.cookies.items()):
        if k == '__ac':
            continue
        cookies[k] = repr(v)
    return cookies


def _get_form_from_request(request):
    form = dict()
    for k, v in _filterPasswordFields(request.form.items()):
        form[k] = repr(v)
    return form


def _get_headers_from_request(request):
    # ensure that all header key-value pairs are strings
    headers = dict()
    for k, v in request.environ.items():
        if not isinstance(v, str):
            v = str(v)
        if k == "HTTP_USER_AGENT":
            k = "User-Agent"
        elif k == "QUERY_STRING":
            k = "query_string"
        headers[k] = v

    return headers


def _set_tags_from_request(scope, request):
    configuration = getConfiguration()
    tags = dict()
    instancehome = configuration.instancehome
    tags["instance_name"] = instancehome.rsplit(os.path.sep, 1)[-1]
    tags["url"] = request.get("ACTUAL_URL")

    for k, v in tags.items():
        scope.set_tag(k, v)


def _prepare_scope_and_event(request, scope, event=None):
    scope.set_context("other", _get_other_from_request(request))
    scope.set_context("lazy items", _get_lazyitems_from_request(request))
    scope.set_context("cookies", _get_cookies_from_request(request))
    scope.set_context("form", _get_form_from_request(request))
    scope.set_context("headers", _get_headers_from_request(request))
    user_info = _get_user_from_request(request)
    scope.set_context("user", user_info)
    if user_info and "id" in user_info:
        scope.user = user_info

    _set_tags_from_request(scope, request)

    if event:
        # # XXX: Force the user-agent into the event, so it gets picked up later.
        event['request'] = {"headers": {'user-agent': request.get("HTTP_USER_AGENT")}}


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
        """ Log an exception and send the info to sentry """
        exc_info = sys.exc_info()
        res = SiteErrorLog.raising(self, info)
        send_anyway = os.environ.get(SEND_ANYWAY_ENV_VAR, '')
        if getConfiguration().debug_mode and not send_anyway:
            # We are in debug mode, do not send tb to Sentry
            logger.info('Zope is in debug mode. Not sending error to sentry')
            return res

        dsn = self.getsentry_dsn
        dsn = dsn and dsn or os.environ.get(DSN_ENV_VAR, '')
        if not dsn:
            logger.warning('Missing DSN. Unable to send errors to sentry')
            return res

        if res is not None:
            client = get_or_create_client(dsn)
            event, hint = event_from_exception(exc_info, client_options=client.options)
            hub = Hub.current
            hub.start_session()

            with sentry_sdk.push_scope() as scope:
                request = getattr(self, 'REQUEST', None)
                if not request:
                    request = getRequest()

                _prepare_scope_and_event(request, scope, event)
                sentry_sdk.capture_event(event, hint, scope)
            hub.end_session()

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


def captureMessage(message, **kwargs):
    site = api.portal.get()
    dsn = site.error_log.getsentry_dsn
    dsn = dsn and dsn or os.environ.get(DSN_ENV_VAR, '')
    if dsn:
        client = get_or_create_client(dsn)
        if client:
            with sentry_sdk.push_scope() as scope:
                request = getattr(site, 'REQUEST', None)
                if not request:
                    request = getRequest()

                _prepare_scope_and_event(request, scope)
                if kwargs:
                    for k,v in kwargs.items():
                        scope.set_extra(k,v)
                sentry_sdk.capture_message(message)


def captureBreadcrumb(**kwargs):
    site = api.portal.get()
    dsn = site.error_log.getsentry_dsn
    dsn = dsn and dsn or os.environ.get(DSN_ENV_VAR, '')
    if dsn:
        client = get_or_create_client(dsn)
        if client:
            sentry_sdk.add_breadcrumb(**kwargs)


def breadcrumb(message, category, level='info', include_result=False):

    def decorator_breadcrumb(func):

        @functools.wraps(func)
        def wrapper_breadcrumb(*args, **kwargs):
            value = func(*args, **kwargs)

            site = api.portal.get()
            dsn = site.error_log.getsentry_dsn
            dsn = dsn and dsn or os.environ.get(DSN_ENV_VAR, '')
            if dsn:
                client = get_or_create_client(dsn)
                if client:
                    data = {'args': args, 'kwargs': kwargs}
                    if include_result:
                        data['result'] = value

                    sentry_sdk.add_breadcrumb(
                        message=message,
                        category=category,
                        level=level,
                        data=data)

            return value

        return wrapper_breadcrumb
    return decorator_breadcrumb
