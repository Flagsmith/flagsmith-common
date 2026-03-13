from unittest.mock import patch

from common.core.sentry import sentry_processor


def test_sentry_processor__context_set__includes_non_meta_fields() -> None:
    # Given
    event_dict = {
        "event": "something happened",
        "level": "error",
        "timestamp": "2024-01-01T00:00:00",
        "environment_id": "123",
        "extra_field": "value",
    }

    # When
    with patch("common.core.sentry.sentry_sdk") as mock_sentry:
        result = sentry_processor(None, "error", event_dict)

    # Then
    assert result is event_dict
    mock_sentry.set_context.assert_called_once_with(
        "structlog",
        {
            "environment_id": "123",
            "extra_field": "value",
        },
    )


def test_sentry_processor__meta_fields_present__excludes_from_context() -> None:
    # Given
    event_dict = {
        "event": "test",
        "level": "info",
        "timestamp": "2024-01-01T00:00:00",
        "_record": "internal",
        "custom_field": "keep_me",
    }

    # When
    with patch("common.core.sentry.sentry_sdk") as mock_sentry:
        sentry_processor(None, "info", event_dict)

    # Then
    context = mock_sentry.set_context.call_args[0][1]
    assert "event" not in context
    assert "level" not in context
    assert "timestamp" not in context
    assert "_record" not in context
    assert context["custom_field"] == "keep_me"
