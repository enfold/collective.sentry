# -*- coding: utf-8 -*-
import logging
from Products.Five import BrowserView
from collective.sentry.error_log import captureMessage
from collective.sentry.error_log import captureBreadcrumb


logger = logging.getLogger('collective.sentry.browser.test_exceptions')


class TestExceptionObject(object):

    attr1 = "Attribute 1"
    attr2 = "Attribute 2"


TEST_JS ="""
<html>
<head>
<script type="text/javascript" src="{url}/++resource++enfold.getsentrylog/vendor/sentry/bundle.min.js"></script>
<script type="text/javascript" src="{url}/sentry.config.js"></script>
<script type="text/javascript" src="{url}/++resource++enfold.getsentrylog/broken_js.js"></script>
</head>
</html>
"""

class TestExceptionsView(BrowserView):
    """
    """

    def raise_exc(self):
        exc_type = self.request.get('exc_type', "AttributeError")
        if exc_type == "AttributeError":
            obj = TestExceptionObject()
            obj.attr3

        elif exc_type == "KeyError":
            test_dict = {
                'key1': "Some value",
                'key2': "Another value"
            }

            test_dict['key3']

        elif exc_type == "TypeError":
            obj = TestExceptionObject(1)

        elif exc_type == "IOError":
            file('/sentry/non-existant/file', 'r')

        elif exc_type == "Javascript":
            return TEST_JS.format(url=self.context.absolute_url())

        else:
            # If unrecognized exception, just raise a NameError
            non_existant_variable

    def very_specific_function(self):
        # do something
        data = {
            'custom_data': True,
            'foo': 'bar'
        }
        captureBreadcrumb(message='Very specific message',
                          category='Category X',
                          level='info',
                          data=data)
        self.raise_exc()

    def __call__(self):
        capture_message = self.request.get('capture_message', False)
        if capture_message:
            captureMessage('This is a custom message',
                           extra={
                               'user': 'joe',
                               'foo': 'bar'
                           })
            return

        capture_breadcrumbs = self.request.get('capture_breadcrumbs', False)
        if capture_breadcrumbs:
            self.very_specific_function()
            return

        self.raise_exc()