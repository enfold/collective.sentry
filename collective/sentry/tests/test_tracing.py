"""Tests for collective.sentry.tracing.

Plain ``unittest``: the module needs neither Plone nor a Sentry client, only
``sentry_sdk`` and (for the trace cases) ``opentelemetry-api``, which the
``[opentelemetry]`` extra installs. Run with ``python -m unittest`` from an
environment that has the package.
"""

import json
import os
import unittest

try:
    from urllib.parse import parse_qs
    from urllib.parse import urlparse
except ImportError:  # pragma: no cover - Python 2
    from urlparse import parse_qs
    from urlparse import urlparse

import sentry_sdk
from sentry_sdk import scope as sentry_scope

from collective.sentry import tracing


TRACE_ID = '4bf92f3577b34da6a3ce929d0e0e4736'
SPAN_ID = '00f067aa0ba902b7'


def otel_span_context():
    """An activated span with a known id, as the WSGI middleware would leave it."""
    from opentelemetry import trace

    span = trace.NonRecordingSpan(
        trace.SpanContext(
            trace_id=int(TRACE_ID, 16),
            span_id=int(SPAN_ID, 16),
            is_remote=False,
            trace_flags=trace.TraceFlags(trace.TraceFlags.SAMPLED),
        )
    )
    return trace.use_span(span)


class EnvironmentMixin(object):

    def setUp(self):
        super(EnvironmentMixin, self).setUp()
        self._environ = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._environ)
        super(EnvironmentMixin, self).tearDown()


class GrafanaURLTests(EnvironmentMixin, unittest.TestCase):

    def test_no_link_without_a_grafana_url(self):
        os.environ.pop(tracing.GRAFANA_URL_ENV_VAR, None)
        self.assertIsNone(tracing.grafana_trace_url(TRACE_ID))

    def test_link_opens_the_trace_in_explore(self):
        os.environ[tracing.GRAFANA_URL_ENV_VAR] = 'https://grafana.example.com/'
        os.environ.pop(tracing.TRACE_DATASOURCE_ENV_VAR, None)

        url = tracing.grafana_trace_url(TRACE_ID, now=1_700_000_000)

        parsed = urlparse(url)
        self.assertEqual(parsed.netloc, 'grafana.example.com')
        self.assertEqual(parsed.path, '/explore')
        query = parse_qs(parsed.query)
        self.assertEqual(query['schemaVersion'], ['1'])
        self.assertEqual(query['orgId'], ['1'])
        panes = json.loads(query['panes'][0])
        pane = panes['trace']
        self.assertEqual(pane['datasource'], 'tempo')
        (q,) = pane['queries']
        self.assertEqual(q['query'], TRACE_ID)
        self.assertEqual(q['queryType'], 'traceql')
        self.assertEqual(q['datasource'], {'type': 'tempo', 'uid': 'tempo'})
        self.assertEqual(
            pane['range'],
            {'from': str(1_700_000_000_000 - tracing.TRACE_RANGE_MS),
             'to': str(1_700_000_000_000 + tracing.TRACE_RANGE_MS)},
        )

    def test_datasource_uid_is_configurable(self):
        os.environ[tracing.GRAFANA_URL_ENV_VAR] = 'https://grafana.example.org'
        os.environ[tracing.TRACE_DATASOURCE_ENV_VAR] = 'tempo-prod'

        url = tracing.grafana_trace_url(TRACE_ID, now=0)

        pane = json.loads(parse_qs(urlparse(url).query)['panes'][0])['trace']
        self.assertEqual(pane['datasource'], 'tempo-prod')
        self.assertEqual(pane['queries'][0]['datasource']['uid'], 'tempo-prod')


@unittest.skipUnless(tracing.available(), 'opentelemetry-api is not installed')
class CurrentTraceTests(unittest.TestCase):

    def test_none_outside_a_span(self):
        self.assertIsNone(tracing.current_trace())

    def test_ids_of_the_current_span(self):
        with otel_span_context():
            self.assertEqual(tracing.current_trace(), (TRACE_ID, SPAN_ID))


@unittest.skipUnless(tracing.available(), 'opentelemetry-api is not installed')
class RegisterTests(unittest.TestCase):

    def setUp(self):
        self._previous = sentry_scope._external_propagation_context_fn
        self._registered = tracing._registered

    def tearDown(self):
        sentry_scope._external_propagation_context_fn = self._previous
        tracing._registered = self._registered

    def test_register_is_idempotent(self):
        self.assertTrue(tracing.register())
        self.assertTrue(tracing.register())
        self.assertIs(sentry_scope._external_propagation_context_fn, tracing.current_trace)

    def test_events_take_the_otel_trace_id(self):
        """The whole point: a captured event's trace context is the OTel trace."""
        tracing.register()
        with otel_span_context():
            context = sentry_sdk.get_isolation_scope().get_trace_context()
        self.assertEqual(context['trace_id'], TRACE_ID)
        self.assertEqual(context['span_id'], SPAN_ID)

    def test_events_outside_a_span_keep_sentrys_own_id(self):
        tracing.register()
        context = sentry_sdk.get_isolation_scope().get_trace_context()
        self.assertNotEqual(context['trace_id'], TRACE_ID)
        self.assertEqual(len(context['trace_id']), 32)


if __name__ == '__main__':
    unittest.main()
