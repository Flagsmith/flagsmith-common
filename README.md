# flagsmith-common
Flagsmith's common library

### Development Setup

This project uses [Poetry](https://python-poetry.org/) for dependency management and includes a Makefile to simplify common development tasks.

#### Prerequisites

- Python >= 3.10
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

By default, Poetry version 2.0.1 will be installed. You can specify a different version:

```bash
make install-poetry POETRY_VERSION=2.1.0
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

1. Add `"common.core"` to `INSTALLED_APPS` in your settings module.
This enables the `start` management command.

2. Add `"common.gunicorn.middleware.PrometheusGunicornLoggerMiddleware"` to `MIDDLEWARE` in your settings module. This enables the `path` label for Prometheus HTTP metrics.

#### Metrics

Flagsmith uses Prometheus to export backend metrics.

The following default metrics are exposed:

- `flagsmith_build_info`: Gauge with a constant value of `1.0`. Labeled with `ci_commit_sha` and `version`.
- `http_request_duration_seconds`: Histogram labeled with `method`, `path`, and `response_status`.
- `http_requests_total`: Counter labeled with `method`, `path`, and `response_status`.

##### Guidelines

Try to come up with meaningful metrics to cover your feature with when developing it. Refer to [Prometheus best practices](https://prometheus.io/docs/practices/naming/) when naming your metric and labels.

Define your metrics in a `metrics.py` module of your Django application (see [example](https://github.com/Flagsmith/flagsmith-common/blob/main/src/common/gunicorn/metrics.py)). Contrary to Prometheus Python client examples and documentation, please name a metric variable exactly as your metric name.

The Prometheus client runs in multi-process mode to accommodate for Gunicorn's [server model](https://docs.gunicorn.org/en/stable/design.html#server-model). When defining a `Gauge` metric, select the appropriate `multiprocess_mode` for it. Refer to the [Metrics tuning](https://prometheus.github.io/client_python/multiprocess/) section of Prometheus Python client documentation. Usually, the appropriate mode is `livesum`, which aggregates values from all live Gunicorn workers.

Flagsmith assumes missing or null metric label values as unknown, and converts them to an `"unknown"` constant value. To support the convention, use the `with_labels` utility function when labelling your metric sample:

```python
from common.prometheus.utils import with_labels

from yourapp import metrics

def get_galaxy() -> str | None: ...

with_labels(
    metrics.planets_in_universe_total,
    galaxy=get_galaxy()
).inc(1)
```
