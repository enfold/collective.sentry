Installation
============

- Add collective.sentry to the eggs attribute in your buildout config.
- Run buildout and (re)start Zope.
- Use the quick installer to install collective.sentry.
- Configure the getsentry DSN to enable getsentry logging.

Upgrade steps
-------------

If you are running a previous version of collective.sentry, please make
sure that you have the latest version installed in the Plone add-ons control
panel. If you see a version update required at the top of the add-ons page,
be sure to click on the update button, or Javascript tracking will not work.

Buildout Configuration Example
------------------------------

Add the collective.sentry to the eggs attribute of the zope instance
section(s) of your buildout::

    [instance]
    ...
    eggs =
        ...
        collective.sentry

DSN Configuration
-----------------

In order for getsentry logging to work you must first creata an account on and
obtain a DSN from sentry.io.  Once you have obtained a DSN you can either
set the environment variable GETSENTRY_DSN to your DSN or configure the DSN on
the error_log from the ZMI after installing the package from the quick
installer.  If set the GETSENTRY_DSN environment variable will be used if the
DSN isn't configured directly on the error_log.

NOTE that setting the DSN in the error log ony works for logging
errors. If you need to use the advanced features of this package, it's
necessary to use the environment variables for now.

Environments
------------

Sentry supports grouping error reports by environment. Collective.sentry
will set the appropriate parameter in the error report to the specified
environment if the GETSENTRY_ENVIRONMENT variable is set:

environment-vars =
    GETSENTRY_ENVIRONMENT Staging

Releases
--------

Sentry also supports release tracking. Collective.sentry will set the
appropriate parameter if the GETSENTRY_RELEASE variable is set:

environment-vars =
    GETSENTRY_RELEASE 2.0a

The best identifier to use for a release is a git commit id, since Sentry
projects can connect to repositories and show release information. More
information about that is in the Sentry documentation.

Breadcrumbs
-----------

Breadcrumbs are a trail of events which happened prior to an error report.
Sentry automatically captures many Zope/Plone breadcrumbs, but an
application could leave more specific breadcrumbs for ease of debugging.

Collective.sentry includes a @breadcrumb decorator which can be used to
easily leave breadcrumbs. Any function or method decorated in this way
will leave a breadcrumb. Example:

from collective.sentry.error_log import breadcrumb

@breadcrumb(message='Dangerous method',
            category='MyApp',
            level='Warning',
            include_result=False)
def dangerous(self):
    ...

The only parameter that requires explanation is include_result. If True,
the result of the function will be included in the breadcrumb data. The
default is False, to avoid cluttering the log with unneeded information.

Sometimes, you might want to include very specific information in a
breadcrumb. In that case, you can use captureBreadcrumb:

from collective.sentry.error_log import captureBreadcrumb

def very_specific_function():
    # do something
    data = ...
    captureBreadcrumb(message='Very specific message',
                      category='Category X',
                      data=data)

Sending custom events
---------------------

Collective.sentry allows sending custom events to Sentry. This can be
useful when there is no exception raised, but there is a condition that
should not be reached. Use captureMessage for this:

from collective.sentry.error_log import captureMessage

def unhealthy_condition():
    if condition:
        captureMessage('We should not be here at all', extra={'user', 'joe'})

Include any additional information that should show up in the error report
using the extra parameter.

Sending Notifications from collective.celery Tasks
--------------------------------------------------

When running collective.celery tasks, the error log is bypassed when errors
occur during a task. Collective.sentry has a hook to register the sentry
client with collective.celery. However, the hook will ONLY work if the
GETSENTRY_DSN environment variable is set. In other words, for
collective.sentry to log errors from celery tasks, using the GETSENTRY_DSN
variable is REQUIRED.

Javascript
----------

Sentry also supports reporting Javascript errors, and collective.sentry
provides support for this as well.
Just go to the error_log control panel (or ZMI), enable the checkbox for
"Track Javascript Errors", and that's it, collective.sentry
will handle the rest.
In order to get the most out of the Javascript report, you can use Sourcemaps[0]
with your Javascript files, since Sentry supports them[1]
Also, if the checkbox for JS tracking is not enabled, you can set the
GETSENTRY_TRACK_JS environment variable in order to enable JS tracking.

User information in Javascript
++++++++++++++++++++++++++++++

collective.sentry will get the authenticated user, if any, and include its
id and email to be sent along with the error.
If your project has a special way of getting this information for users, you
will need to register an adapter implementing the
`collective.sentry.browser.interfaces.IUserInfo` interface. All you need
is to provide a method `get_user_data` that should return a dict structure
with `{'id': user_id_in_system, 'email': user_email}`.

Filter Javascript errors
++++++++++++++++++++++++

Collective.sentry can filter errors that are not caused by your
applications, or errors that you want to ignore for other reasons. If you
set the 'GETSENTRY_JS_ERRORS_TO_IGNORE' to a comma-separated list of
regex patterns or strings, any matching errors will not be reported.

Example (in buildout.cfg):

environment-vars =
    GETSENTRY_JS_ERRORS_TO_IGNORE /^Exact Error Match$/, /error_fragment/

Ignore certain urls
+++++++++++++++++++

It is possible to ignore urls and report only errors that do not match an
url pattern. Use the GETSENTRY_JS_TO_IGNORE environment variable for this.

environment-vars =
    GETSENTRY_JS_TO_IGNORE /sentry\.io/, 'http://mysite.com/script.js'

Alternatively, there are cases where you would only want to collect
Javascript errors coming from specific urls. To do this, set the
GETSENTRY_JS_TO_ALLOW variable:

environment-vars =
    GETSENTRY_JS_TO_ALLOW /important_js/, 'http://mysite.com/app.js'

User Feedback support
---------------------

Sentry allows users to be presented with a dialog box for sending error
feedback when an error page is shown. The feedback is added to the sentry
report. In collective.sentry, you can enable user feedback when the
GETSENTRY_USER_FEEDBACK variable is set to true. Because sentry uses the
Raven Javascript client to show the dialog, you must also have the
GETSENTRY_TRACK_JS variable set to true for this to work:

environment-vars =
    GETSENTRY_TRACK_JS true
    GETSENTRY_USER_FEEDBACK true

Debug Mode
----------

When developing a site, or when starting a debug instance to fix an issue, you
usually don't want to pollute Sentry Stream with errors caused by debugging.
collective.sentry will not send errors to sentry if the instance is in
debug mode.
If you want to send errors anyway, you can set the GETSENTRY_ALWAYS_SEND
environment variable, to ignore this condition and send the errors anyway.

Notes
-----

After an exception event is sent to sentry.io the error log will not send
another exception event of the same type from the same error log if the new
exception occurs within 3 minutes of the first exception.

[0] - http://www.html5rocks.com/en/tutorials/developertools/sourcemaps/
[1] - https://www.getsentry.com/docs/sourcemaps/
