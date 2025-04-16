# flagsmith-common
Flagsmith's common library

### Development Setup

This project uses [Poetry](https://python-poetry.org/) for dependency management and includes a Makefile to simplify common development tasks.

#### Prerequisites

- Python >= 3.11
- Make

#### Installation

You can set up your development environment using the provided Makefile:

```bash
# Install everything (pip, poetry, and project dependencies)
make install

# Individual installation steps are also available
make install-pip       # Upgrade pip
make install-poetry    # Install Poetry
make install-packages  # Install project dependencies
```

#### Development

Run linting checks using pre-commit:

```bash
make lint
```

Additional options can be passed to the `install-packages` target:

```bash
# Install with development dependencies
make install-packages opts="--with dev"

# Install with specific extras
make install-packages opts="--extras 'feature1 feature2'"
```

### Usage

#### Installation

1. To make use of the `test_tools` Pytest plugin, install the packages with the `test-tools` extra, e.g. `pip install flagsmith-common[test-tools]`.

2. Make sure `"common.core"` is in the `INSTALLED_APPS` of your settings module.
This enables the `manage.py flagsmith` commands.

3. Add `"common.gunicorn.middleware.RouteLoggerMiddleware"` to `MIDDLEWARE` in your settings module.
This enables the `route` label for Prometheus HTTP metrics.

4. To enable the `/metrics` endpoint, set the `PROMETHEUS_ENABLED` setting to `True`.

#### Test tools

##### Fixtures

###### `assert_metric`

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

###### `saas_mode`

The `saas_mode` fixture makes all `common.core.utils.is_saas` calls return `True`.

###### `enterprise_mode`

The `enterprise_mode` fixture makes all `common.core.utils.is_enterprise` calls return `True`.

##### Markers

###### `pytest.mark.saas_mode`

Use this mark to auto-use the `saas_mode` fixture.

###### `pytest.mark.enterprise_mode`

Use this mark to auto-use the `enterprise_mode` fixture.

#### Metrics

Flagsmith uses Prometheus to track performance metrics.

The following default metrics are exposed:

##### Common metrics

- `flagsmith_build_info`: Has the labels `version` and `ci_commit_sha`.
- `flagsmith_http_server_request_duration_seconds`: Histogram labeled with `method`, `route`, and `response_status`.
- `flagsmith_http_server_requests_total`: Counter labeled with `method`, `route`, and `response_status`.
- `flagsmith_http_server_response_size_bytes`:Histogram labeled with `method`, `route`, and `response_status`.
- `flagsmith_task_processor_enqueued_tasks_total`: Counter labeled with `task_identifier`.

##### Task Processor metrics

- `flagsmith_task_processor_finished_tasks_total`: Counter labeled with `task_identifier`, `task_type` (`"recurring"`, `"standard"`) and `result` (`"success"`, `"failure"`).
- `flagsmith_task_processor_task_duration_seconds`: Histogram labeled with `task_identifier`, `task_type` (`"recurring"`, `"standard"`) and `result` (`"success"`, `"failure"`).

##### Guidelines

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
