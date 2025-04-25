# Prometheus metrics

Flagsmith exports Prometheus metrics described below.
{% for metric in flagsmith_metrics %}
## `{{ metric.name }}` {{ metric.type }}

{{ metric.documentation }}

Labels:
{% for label in metric.labels %} - `{{ label }}`
{% endfor %}{% endfor %}
