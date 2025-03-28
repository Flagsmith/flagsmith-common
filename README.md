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

1. Make sure `"common.core"` is in the `INSTALLED_APPS` of your settings module.
This enables the `manage.py flagsmith` commands.

2. Add `"common.gunicorn.middleware.RouteLoggerMiddleware"` to `MIDDLEWARE` in your settings module.
This enables the `route` label for Prometheus HTTP metrics.

3. To enable the `/metrics` endpoint, set the `PROMETHEUS_ENABLED` setting to `True`.

#### Metrics

Flagsmith uses Prometheus to track performance metrics.

The following default metrics are exposed:

- `flagsmith_build_info`: Has the labels `version` and `ci_commit_sha`.
- `http_server_request_duration_seconds`: Histogram labeled with `method`, `route`, and `response_status`.
- `http_server_requests_total`: Counter labeled with `method`, `route`, and `response_status`.

##### Guidelines

Try to come up with meaningful metrics to cover your feature with when developing it. Refer to [Prometheus best practices][1] when naming your metric and labels.

Define your metrics in a `metrics.py` module of your Django application — see [example][2]. Contrary to Prometheus Python client examples and documentation, please name a metric variable exactly as your metric name.

It's generally a good idea to allow users to define histogram buckets of their own. Flagsmith accepts a `PROMETHEUS_HISTOGRAM_BUCKETS` setting so users can customise their buckets. To honour the setting, use the `common.prometheus.Histogram` class when defining your histograms. When using `prometheus_client.Histogram` directly, please expose a dedicated setting like so:

```python
import prometheus_client
from django.conf import settings

distance_from_earth_au = prometheus.Histogram(
    "distance_from_earth_au",
    "Distance from Earth in astronomical units",
    buckets=settings.DISTANCE_FROM_EARTH_AU_HISTOGRAM_BUCKETS,
)
```

[1]: https://prometheus.io/docs/practices/naming/
[2]: https://github.com/Flagsmith/flagsmith-common/blob/main/src/common/gunicorn/metrics.py
[3]: https://docs.gunicorn.org/en/stable/design.html#server-model
[4]: https://prometheus.github.io/client_python/multiprocess
