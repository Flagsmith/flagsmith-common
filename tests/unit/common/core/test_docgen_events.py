from pathlib import Path

from common.core.docgen.events import (
    EventEntry,
    SourceLocation,
    get_event_entries_from_source,
)


def test_get_event_entries_from_source__literal_domain_plain_info__records_single_entry() -> (
    None
):
    # Given
    source = (
        "import structlog\n"
        "\n"
        'logger = structlog.get_logger("code_references")\n'
        'logger.info("scan.created")\n'
    )
    path = Path("projects/code_references/views.py")

    # When
    entries = list(
        get_event_entries_from_source(
            source,
            module_dotted="projects.code_references.views",
            path=path,
        )
    )

    # Then
    assert entries == [
        EventEntry(
            name="code_references.scan.created",
            level="info",
            attributes=frozenset(),
            locations=[SourceLocation(path=path, line=4)],
        ),
    ]
