#
from Products.SiteErrorLog.SiteErrorLog import use_error_logging
from collective.sentry import error_log

def initialize(context):
    context.registerClass(error_log.GetSentryErrorLog,
            constructors=(error_log.manage_addErrorLog,),
            permission=use_error_logging,
            icon='error.gif')
