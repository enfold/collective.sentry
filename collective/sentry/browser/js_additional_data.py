from collective.sentry.browser.interfaces import IUserInfo
from zope.interface import implementer


@implementer(IUserInfo)
class DefaultUserInfo(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get_user_data(self):
        result = None
        if not self.context.portal_membership.isAnonymousUser():
            user = self.context.portal_membership.getAuthenticatedMember()
            result = {'id': user.getId()}
            email = user.getProperty('email', None)
            if email:
                result['email'] = email

        return result
