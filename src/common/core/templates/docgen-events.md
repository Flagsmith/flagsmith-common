{% for event in flagsmith_events %}
### `{{ event.name }}`

Logged at `{{ event.level }}` from:
{% for location in event.locations %} - `{{ location.path }}:{{ location.line }}`
{% endfor %}
Attributes:
{% for attr in event.attributes %} - `{{ attr }}`
{% endfor %}{% endfor %}
