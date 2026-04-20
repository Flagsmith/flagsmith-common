---
title: Events
sidebar_label: Events
sidebar_position: 30
---

Flagsmith backend emits [OpenTelemetry events](https://opentelemetry.io/docs/specs/otel/logs/data-model/#events)
that can be ingested to downstream observability systems and/or a data warehouse of your choice via OTLP.
To learn how to configure this, see [OpenTelemetry](deployment-self-hosting/scaling-and-performance/opentelemetry).

## Event catalogue
{% for event in flagsmith_events %}
### `{{ event.name }}`

Logged at `{{ event.level }}` from:
{% for location in event.locations %} - `{{ location.path }}:{{ location.line }}`
{% endfor %}
Attributes:
{% for attr in event.attributes %} - `{{ attr }}`
{% endfor %}{% endfor %}
