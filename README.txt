Installation
============

- Add collective.sentry to the eggs attribute in your buildout config.
- Run buildout and (re)start Zope.
- Use the quick installer to install collective.sentry.
- Configure the getsentry DSN to enable getsentry logging.

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
obtain a DSN from getsentry.com.  Once you have obtained a DSN you can either
set the environment variable GETSENTRY_DSN to your DSN or configure the DSN on
the error_log from the ZMI after installing the package from the quick
installer.  If set the GETSENTRY_DSN environment variable will be used if the
DSN isn't configured directly on the error_log.

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

GetSentry also supports reporting Javascript errors, and collective.sentry
provides support for this as well.
Just go to the error_log control panel (or ZMI), enable the checkbox for
"Track Javascript Errors", and that's it, collective.sentry
will handle the rest.
In order to get the most out of the Javascript report, you can use Sourcemaps[0]
with your Javascript files, since GetSentry supports them[1]
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

Filter what to send
+++++++++++++++++++

Sometimes, visitors will get to your site using very old, unsupported browsers.
You don't want them to spam your GetSentry stream with errors from them.
For this, you can define a `GetSentryDoNotSend` global variable in your
Javascript. If this variable is declared, and set to `true`, errors will not
be sent to GetSentry.

Ignore certain files
++++++++++++++++++++

Javascript tracking works by wrapping the code in a big `try` block. If any
error happens, it will be sent to GetSentry when it is catched.
You can provide a list of files to not be wrapped with this block by setting the
GETSENTRY_JS_TO_IGNORE environment variable.

Implementation is very naive at the moment, and it will only check if the string
is in the url. For example, providing:

'getsentry.js'

will match 'http://www.host.com/js/getsentry.js' but not
'http://www.host.com/js/getsentry-cachekey.js'

However providing:

'getsentry'

will match 'http://www.host.com/js/getsentry.js' and also
'http://www.host.com/js/getsentry-cachekey.js' as well.

NOTE: Be careful because this will match the string appearing *anywhere* in the
url.

Several strings can be provided, separated by a semi-colon (;)


Debug Mode
----------

When developing a site, or when starting a debug instance to fix an issue, you
usually don't want to pollute GetSentry Stream with errors caused by debugging.
collective.sentry will not send errors to sentry if the instance is in
debug mode.
If you want to send errors anyway, you can set the GETSENTRY_ALWAYS_SEND
environment variable, to ignore this condition and send the errors anyway.

Notes
-----

After an exception event is sent to getsentry.com the error log will not send
another exception event of the same type from the same error log if the new
exception occurs within 3 minutes of the first exception.

[0] - http://www.html5rocks.com/en/tutorials/developertools/sourcemaps/
[1] - https://www.getsentry.com/docs/sourcemaps/
