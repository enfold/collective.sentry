from zope.interface import Interface


class IUserInfo(Interface):
    """
    """

    def get_user_data():
        """ This function should return a dict with the structure expected
        by Raven to send user data along with the errors. More info:
        http://raven-js.readthedocs.org/en/latest/usage/#tracking-authenticated-users
        """
