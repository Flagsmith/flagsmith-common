from pathlib import Path

import pytest

from common.core.docgen.events import (
    DocgenEventsWarning,
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
        pytest.param(
            """\
import structlog

logger = structlog.get_logger(__name__)
logger.info("something.happened")
""",
            [
                EventEntry(
                    name=f"{MODULE_DOTTED}.something.happened",
                    level="info",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=4)],
                ),
            ],
            id="dunder-name-resolves-to-module-dotted",
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


def test_get_event_entries_from_source__non_resolvable_domain__warns_and_skips() -> (
    None
):
    # Given
    source = """\
import structlog

domain = "sneaky"
logger = structlog.get_logger(domain)
logger.info("something.happened")
"""

    # When
    with pytest.warns(DocgenEventsWarning, match="domain") as warning_records:
        entries = list(
            get_event_entries_from_source(
                source,
                module_dotted=MODULE_DOTTED,
                path=PATH,
            )
        )

    # Then
    assert entries == []
    assert len(warning_records) == 1
    assert str(PATH) in str(warning_records[0].message)
