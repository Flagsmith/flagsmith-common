# flagsmith-common

[![Coverage](https://codecov.io/gh/Flagsmith/flagsmith-common/graph/badge.svg?token=L3OGOXH86K)](https://codecov.io/gh/Flagsmith/flagsmith-common)

Flagsmith's common library

## Local development

The project assumes the following tools installed:

- [uv](https://github.com/astral-sh/uv)
- [GNU Make](https://www.gnu.org/software/make/)

To list available Makefile targets, run `make help`.

To set up local development environment, run `make install`.

To run linters, run `make lint`.

To run tests, run `make test`.

## Usage

### Installation

1. Install all runtime packages: `uv add flagsmith-common[common-core,task-processor]`

2. To enable the Pytest fixtures, run `uv add --G dev flagsmith-common[test-tools]`. Skipping this step will make Pytest collection fail due to missing dependencies.

3. Make sure `"common.core"` is in the `INSTALLED_APPS` of your settings module.
This enables the `manage.py flagsmith` commands.

4. Add `"common.gunicorn.middleware.RouteLoggerMiddleware"` to `MIDDLEWARE` in your settings module.
This enables the `route` label for Prometheus HTTP metrics.

5. To enable the `/metrics` endpoint, set the `PROMETHEUS_ENABLED` setting to `True`.

### Pre-commit hooks

This repo provides a [`flagsmith-lint-tests`](.pre-commit-hooks.yaml) hook that enforces test conventions:

- **FT001**: No module-level `Test*` classes — use function-based tests
- **FT002**: No `import unittest` / `from unittest import TestCase` — use pytest (`unittest.mock` is fine)
- **FT003**: Test names must follow `test_{subject}__{condition}__{expected}`
- **FT004**: Test bodies must contain `# Given`, `# When`, and `# Then` comments

To use in your repo, add to `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/Flagsmith/flagsmith-common
  rev: main
  hooks:
    - id: flagsmith-lint-tests
```

Use `# noqa: FT003` (or any code) inline to suppress individual violations.

### Test tools

#### Fixtures

##### `assert_metric`

To test your metrics using the `assert_metric` fixture:

```python
from common.test_tools import AssertMetricFixture

def test_my_code__expected_metrics(assert_metric: AssertMetricFixture) -> None:
    # When
    my_code()

    # Then
    assert_metric(
        name="flagsmith_distance_from_earth_au_sum",
        labels={"engine_type": "solar_sail"},
        value=1.0,
    )
```

##### `saas_mode`

The `saas_mode` fixture makes all `common.core.utils.is_saas` calls return `True`.

##### `enterprise_mode`

The `enterprise_mode` fixture makes all `common.core.utils.is_enterprise` calls return `True`.

#### Markers

##### `pytest.mark.saas_mode`

Use this mark to auto-use the `saas_mode` fixture.

##### `pytest.mark.enterprise_mode`

Use this mark to auto-use the `enterprise_mode` fixture.

### OpenTelemetry

Flagsmith supports exporting traces and structured logs over OTLP.

#### Configuration

OTel instrumentation is opt-in, controlled by environment variables:

| Variable                          | Description                                                                                                           | Default         |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------- | --------------- |
| `OTEL_EXPORTER_OTLP_ENDPOINT`     | Base OTLP endpoint (e.g. `http://collector:4318`). If unset, no OTel setup occurs and OTel packages are not imported. | _(disabled)_    |
| `OTEL_SERVICE_NAME`               | The `service.name` resource attribute.                                                                                | `flagsmith-api` |
| `OTEL_TRACING_EXCLUDED_URL_PATHS` | Comma-separated URL paths to exclude from tracing (e.g. `health/liveness,health/readiness`).                          | _(none)_        |

Standard `OTEL_*` env vars (e.g. `OTEL_RESOURCE_ATTRIBUTES`, `OTEL_EXPORTER_OTLP_HEADERS`) are also respected by the OTel SDK.

#### What gets configured

When `OTEL_EXPORTER_OTLP_ENDPOINT` is set, `ensure_cli_env()` sets up:

- **Tracing**: `TracerProvider` with OTLP/HTTP span export, W3C `TraceContext` + `Baggage` propagation, and auto-instrumentation for:
  - **Django** (`DjangoInstrumentor`): creates a root span per HTTP request with span names formatted as `{METHOD} {route_template}` (e.g. `GET /api/v1/projects/{pk}/`).
  - **psycopg2** (`Psycopg2Instrumentor`): creates child spans for each SQL query with `db.system`, `db.statement`, and `db.name` attributes. SQL commenter is enabled, adding trace context as SQL comments for database-side correlation.
  - **Redis** (`RedisInstrumentor`): creates child spans for each Redis command with `db.system` and `db.statement` attributes.
- **Structured log export**: A structlog processor that routes log events to an OTLP log endpoint.

#### Emitting OTel log events via structlog

Use structlog as usual. The OTel processor captures events and maps them to OTLP log records:

```python
import structlog

log = structlog.get_logger("code_references")
log.info("scan-created", code_references__count=3, feature__count=2)
```

This produces an OTLP log record with:

- `Body: scan-created`
- `EventName: code_references.scan_created` (logger name + `inflection.underscore` of the event)
- `Severity: INFO`
- `Attributes: code_references.count=3, feature.count=2` (double underscores are converted to dots)
- W3C Baggage entries from the current OTel context are copied into log attributes (e.g. `amplitude.device_id`, `amplitude.session_id`).

### Metrics

Flagsmith uses Prometheus to track performance metrics.

The following default metrics are exposed:

#### Common metrics

- `flagsmith_build_info`: Has the labels `version` and `ci_commit_sha`.
- `flagsmith_http_server_request_duration_seconds`: Histogram labeled with `method`, `route`, and `response_status`.
- `flagsmith_http_server_requests_total`: Counter labeled with `method`, `route`, and `response_status`.
- `flagsmith_http_server_response_size_bytes`: Histogram labeled with `method`, `route`, and `response_status`.
- `flagsmith_task_processor_enqueued_tasks_total`: Counter labeled with `task_identifier`.

#### Task Processor metrics

- `flagsmith_task_processor_finished_tasks_total`: Counter labeled with `task_identifier`, `task_type` (`"recurring"`, `"standard"`) and `result` (`"success"`, `"failure"`).
- `flagsmith_task_processor_task_duration_seconds`: Histogram labeled with `task_identifier`, `task_type` (`"recurring"`, `"standard"`) and `result` (`"success"`, `"failure"`).

#### Guidelines

Try to come up with meaningful metrics to cover your feature with when developing it. Refer to [Prometheus best practices][1] when naming your metric and labels.

As a reasonable default, Flagsmith metrics are expected to be namespaced with the `"flagsmith_"` prefix.

Define your metrics in a `metrics.py` module of your Django application — see [example][2]. Contrary to Prometheus Python client examples and documentation, please name a metric variable exactly as your metric name.

It's generally a good idea to allow users to define histogram buckets of their own. Flagsmith accepts a `PROMETHEUS_HISTOGRAM_BUCKETS` setting so users can customise their buckets. To honour the setting, use the `common.prometheus.Histogram` class when defining your histograms. When using `prometheus_client.Histogram` directly, please expose a dedicated setting like so:

```python
import prometheus_client
from django.conf import settings

flagsmith_distance_from_earth_au = prometheus_client.Histogram(
    "flagsmith_distance_from_earth_au",
    "Distance from Earth in astronomical units",
    labels=["engine_type"],
    buckets=settings.DISTANCE_FROM_EARTH_AU_HISTOGRAM_BUCKETS,
)
```

For testing your metrics, refer to [`assert_metric` documentation][5].

[1]: https://prometheus.io/docs/practices/naming/
[2]: https://github.com/Flagsmith/flagsmith-common/blob/main/src/common/gunicorn/metrics.py
[3]: https://docs.gunicorn.org/en/stable/design.html#server-model
[4]: https://prometheus.github.io/client_python/multiprocess
[5]: #assert_metric
