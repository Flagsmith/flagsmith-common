from pathlib import Path

import pytest

from common.core.docgen.events import (
    EventEntry,
    SourceLocation,
    get_event_entries_from_source,
)

PATH = Path("projects/code_references/views.py")
MODULE_DOTTED = "projects.code_references.views"


@pytest.mark.parametrize(
    "source, expected_entries",
    [
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("code_references")
logger.info("scan.created")
""",
            [
                EventEntry(
                    name="code_references.scan.created",
                    level="info",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=4)],
                ),
            ],
            id="plain-info-no-kwargs",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("code_references")
logger.info(
    "scan.created",
    organisation__id=1,
    code_references__count=2,
    feature__count=3,
)
""",
            [
                EventEntry(
                    name="code_references.scan.created",
                    level="info",
                    attributes=frozenset(
                        {
                            "organisation.id",
                            "code_references.count",
                            "feature.count",
                        }
                    ),
                    locations=[SourceLocation(path=PATH, line=4)],
                ),
            ],
            id="kwargs-with-double-underscore-substitution",
        ),
    ],
)
def test_get_event_entries_from_source__emit_log__expected_entries(
    source: str,
    expected_entries: list[EventEntry],
) -> None:
    # Given / When
    entries = list(
        get_event_entries_from_source(
            source,
            module_dotted=MODULE_DOTTED,
            path=PATH,
        )
    )

    # Then
    assert entries == expected_entries
