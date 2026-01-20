---
title: Metrics
sidebar_label: Metrics
sidebar_position: 20
---

## Prometheus

To enable the Prometheus `/metrics` endpoint, set the `PROMETHEUS_ENABLED` environment variable to `true`.

When enabled, Flagsmith serves the `/metrics` endpoint on port 9100.

The metrics provided by Flagsmith are described below.

{% for metric in flagsmith_metrics %}
### `{{ metric.name }}`

{{ metric.type|title }}.

{{ metric.documentation }}

Labels:
{% for label in metric.labels %} - `{{ label }}`
{% endfor %}{% endfor %}
