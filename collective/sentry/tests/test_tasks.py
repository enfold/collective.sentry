from collective.sentry import tasks
from types import SimpleNamespace
from unittest import mock

import unittest


def starter(environment):
    return SimpleNamespace(cfg=SimpleNamespace(environment=environment))


class TestWorkerHook(unittest.TestCase):

    def test_initialises_sentry_with_the_zope_conf_dsn(self):
        with mock.patch.object(tasks.sentry_sdk, 'init') as init:
            tasks.extra_config(starter({'GETSENTRY_DSN': 'https://key@sentry/1'}))
        init.assert_called_once()
        kwargs = init.call_args.kwargs
        self.assertEqual(kwargs['dsn'], 'https://key@sentry/1')
        # The default integrations (logging among them) report failed jobs.
        self.assertNotIn('integrations', kwargs)

    def test_does_nothing_without_dsn(self):
        with mock.patch.object(tasks.sentry_sdk, 'init') as init:
            tasks.extra_config(starter({}))
            tasks.extra_config(starter(None))
        init.assert_not_called()
