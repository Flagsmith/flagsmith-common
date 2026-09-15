from typing import Any

import pytest


@pytest.fixture()
def feature_state_metadata() -> dict[str, Any]:
    return {
        "experiment": {
            "id": 42,
            "name": "New checkout CTA",
            "in_experiment": True,
        },
        "future_key": {"nested": ["anything"]},
    }
