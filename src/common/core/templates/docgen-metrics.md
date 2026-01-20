---
title: Metrics
sidebar_label: Metrics
sidebar_position: 20
---

## Prometheus

To enable the Prometheus `/metrics` endpoint, set the `PROMETHEUS_ENABLED` environment variable to `true`.

When enabled, Flagsmith serves the `/metrics` endpoint on a standalone HTTP server on port 9100, separate from the main API server. This design ensures that metrics collection remains available even when the main API is under heavy load.

The metrics provided by Flagsmith are described below.

{% for metric in flagsmith_metrics %}
### `{{ metric.name }}`

{{ metric.type|title }}.

{{ metric.documentation }}

Labels:
{% for label in metric.labels %} - `{{ label }}`
{% endfor %}{% endfor %}
