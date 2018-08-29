## Script (Python) "prefs_error_log_setProperties"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=keep_entries,ignored_exceptions,getsentry_dsn,copy_to_zlog=0,track_js=0
##title=
##

from Products.CMFPlone import PloneMessageFactory as _

request = context.REQUEST

context.error_log.setProperties(keep_entries, copy_to_zlog, ignored_exceptions,
        getsentry_dsn, track_js)
context.plone_utils.addPortalMessage(_(u'Changes made.'))

return request.RESPONSE.redirect(context.absolute_url() + '/prefs_error_log_form')
