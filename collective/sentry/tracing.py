"""Link the events this package sends to the request trace behind them.

When the process runs the OpenTelemetry SDK (typically a WSGI middleware that
continues the ``traceparent`` header the request arrived with), every request
carries a W3C trace id that the proxies in front of Plone log at each hop and
that a trace store such as Grafana Tempo keeps. Two things tie a Sentry issue
to it:

* ``register()`` makes sentry-sdk take the ``trace`` context of every event
  from the current OpenTelemetry span instead of inventing an id of its own,
  so the id on the Sentry issue is the one in Grafana. This is sentry-sdk's
  own hook for the purpose (``register_external_propagation_context``, what
  its ``OTLPIntegration`` uses) without the rest of that integration, which
  would export spans to Sentry and replace the W3C propagator.
* ``current_trace()`` and ``grafana_trace_url()`` give ``error_log`` a tag and
  a link to put on the event.

Everything degrades to "no trace": without ``opentelemetry-api`` (the
``collective.sentry[opentelemetry]`` extra), without a configured SDK, or
outside a request, there is no current span and nothing is added.
"""

import json
import os
import time

from sentry_sdk.scope import register_external_propagation_context

try:
    from urllib.parse import urlencode
except ImportError:  # pragma: no cover - Python 2
    from urllib import urlencode

try:
    from opentelemetry.trace import INVALID_SPAN_ID
    from opentelemetry.trace import INVALID_TRACE_ID
    from opentelemetry.trace import format_span_id
    from opentelemetry.trace import format_trace_id
    from opentelemetry.trace import get_current_span
except ImportError:  # the [opentelemetry] extra is not installed
    get_current_span = None


#: Base URL of the Grafana that fronts the trace store, e.g.
#: ``https://grafana.example.com``. Unset: no link on the event.
GRAFANA_URL_ENV_VAR = 'GETSENTRY_GRAFANA_URL'
#: UID of the Grafana data source holding the traces.
TRACE_DATASOURCE_ENV_VAR = 'GETSENTRY_TRACE_DATASOURCE'
DEFAULT_TRACE_DATASOURCE = 'tempo'

#: Half-width of the time range the Grafana link opens on, in milliseconds.
#: The trace store looks an id up within a time range, and the request that produced an
#: error can only have started shortly before the error was reported; an hour
#: either side is generous and keeps the link valid for as long as the trace
#: is retained.
TRACE_RANGE_MS = 60 * 60 * 1000

_registered = False


def available():
    """Is opentelemetry-api importable?"""
    return get_current_span is not None


def current_trace():
    """``(trace_id, span_id)`` of the current span as hex strings, or ``None``.

    ``None`` whenever there is no valid span: no SDK installed, no SDK
    configured, or code running outside a request.
    """
    if get_current_span is None:
        return None
    context = get_current_span().get_span_context()
    if context.trace_id == INVALID_TRACE_ID or context.span_id == INVALID_SPAN_ID:
        return None
    return format_trace_id(context.trace_id), format_span_id(context.span_id)


def grafana_trace_url(trace_id, now=None):
    """A Grafana Explore URL opening ``trace_id`` in the trace data source.

    ``None`` unless ``GETSENTRY_GRAFANA_URL`` is set. ``now`` (seconds since
    the epoch) centres the time range; it defaults to the current time, which
    is when the error is being reported.
    """
    base = os.environ.get(GRAFANA_URL_ENV_VAR, '').strip().rstrip('/')
    if not base:
        return None
    datasource = (
        os.environ.get(TRACE_DATASOURCE_ENV_VAR, '').strip()
        or DEFAULT_TRACE_DATASOURCE
    )
    now_ms = int((time.time() if now is None else now) * 1000)
    pane = {
        'datasource': datasource,
        'queries': [
            {
                'refId': 'A',
                'datasource': {'type': 'tempo', 'uid': datasource},
                'queryType': 'traceql',
                'query': trace_id,
            }
        ],
        'range': {
            'from': str(now_ms - TRACE_RANGE_MS),
            'to': str(now_ms + TRACE_RANGE_MS),
        },
    }
    query = urlencode(
        {
            'schemaVersion': 1,
            'orgId': 1,
            'panes': json.dumps({'trace': pane}, separators=(',', ':')),
        }
    )
    return '{0}/explore?{1}'.format(base, query)


def register():
    """Make sentry-sdk take each event's trace context from OpenTelemetry.

    Idempotent. Returns whether the hook is in place; ``False`` means
    opentelemetry-api is not installed and events keep Sentry's own ids.
    """
    global _registered
    if get_current_span is None:
        return False
    if not _registered:
        register_external_propagation_context(current_trace)
        _registered = True
    return True
