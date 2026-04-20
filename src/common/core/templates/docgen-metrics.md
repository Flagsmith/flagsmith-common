{% for metric in flagsmith_metrics %}
### `{{ metric.name }}`

{{ metric.type|title }}.

{{ metric.documentation }}

Labels:
{% for label in metric.labels %} - `{{ label }}`
{% endfor %}{% endfor %}
