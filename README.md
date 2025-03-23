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

Add `"common.core"` to `INSTALLED_APPS` in your settings module.
This enables the `start` management command.

#### Metrics

Flagsmith uses Prometheus to export backend metrics.

