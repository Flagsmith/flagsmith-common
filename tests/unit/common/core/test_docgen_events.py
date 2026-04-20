import warnings
from pathlib import Path
from unittest.mock import ANY

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem

from common.core.docgen.events import (
    DocgenEventsWarning,
    EventEntry,
    SourceLocation,
    get_event_entries_from_source,
    get_event_entries_from_tree,
    merge_event_entries,
)

PATH = Path("projects/code_references/views.py")
MODULE_DOTTED = "projects.code_references.views"


@pytest.mark.parametrize(
    "source, expected_entries, expected_warnings",
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
            [],
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
            [],
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
            [],
            id="dunder-name-resolves-to-module-dotted",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("code_references")
logger.exception("import.failed")
""",
            [
                EventEntry(
                    name="code_references.import.failed",
                    level="exception",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=4)],
                ),
            ],
            [],
            id="exception-method-is-recognised",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("app_analytics")
logger.warning("no-analytics-database-configured")
""",
            [
                EventEntry(
                    name="app_analytics.no_analytics_database_configured",
                    level="warning",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=4)],
                ),
            ],
            [],
            id="hyphenated-event-body-normalised-to-snake_case",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("segments")
logger.info("NewSegmentRevision")
""",
            [
                EventEntry(
                    name="segments.new_segment_revision",
                    level="info",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=4)],
                ),
            ],
            [],
            id="camel-case-event-body-normalised-to-snake_case",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("sentry_change_tracking")


def track() -> None:
    log = logger.bind(sentry_action="trigger", feature_name="flag")
    log.info("success", response_status=200)
""",
            [
                EventEntry(
                    name="sentry_change_tracking.success",
                    level="info",
                    attributes=frozenset(
                        {"sentry_action", "feature_name", "response_status"}
                    ),
                    locations=[SourceLocation(path=PATH, line=8)],
                ),
            ],
            [],
            id="reassigned-bind-merges-attrs",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("workflows")


def publish() -> None:
    logger.bind(workflow_id=1).info("published", status="ok")
""",
            [
                EventEntry(
                    name="workflows.published",
                    level="info",
                    attributes=frozenset({"workflow_id", "status"}),
                    locations=[SourceLocation(path=PATH, line=7)],
                ),
            ],
            [],
            id="chained-bind-merges-attrs",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("workflows")


def publish() -> None:
    logger.bind(workflow_id=1).bind(actor_id=2).info("published", status="ok")
""",
            [
                EventEntry(
                    name="workflows.published",
                    level="info",
                    attributes=frozenset({"workflow_id", "actor_id", "status"}),
                    locations=[SourceLocation(path=PATH, line=7)],
                ),
            ],
            [],
            id="multi-chained-bind-merges-attrs",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("workflows")


def publish() -> None:
    log = logger.bind(workflow_id=1)
    log = log.bind(actor_id=2)
    log.info("published", status="ok")
""",
            [
                EventEntry(
                    name="workflows.published",
                    level="info",
                    attributes=frozenset({"workflow_id", "actor_id", "status"}),
                    locations=[SourceLocation(path=PATH, line=9)],
                ),
            ],
            [],
            id="self-reassigned-bind-layers-further",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("workflows")


def publish_one() -> None:
    log = logger.bind(one_attr=1)
    log.info("evt.one", kwarg_one=True)


def publish_two() -> None:
    log = logger.bind(two_attr=2)
    log.info("evt.two", kwarg_two=True)
""",
            [
                EventEntry(
                    name="workflows.evt.one",
                    level="info",
                    attributes=frozenset({"one_attr", "kwarg_one"}),
                    locations=[SourceLocation(path=PATH, line=8)],
                ),
                EventEntry(
                    name="workflows.evt.two",
                    level="info",
                    attributes=frozenset({"two_attr", "kwarg_two"}),
                    locations=[SourceLocation(path=PATH, line=13)],
                ),
            ],
            [],
            id="binds-in-different-functions-do-not-leak",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("workflows")


async def publish() -> None:
    log = logger.bind(workflow_id=1)
    log.info("published", status="ok")
""",
            [
                EventEntry(
                    name="workflows.published",
                    level="info",
                    attributes=frozenset({"workflow_id", "status"}),
                    locations=[SourceLocation(path=PATH, line=8)],
                ),
            ],
            [],
            id="bind-inside-async-function",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("code_references")
event_name = "dyn"
logger.bind(a=1).info(event_name)
""",
            [],
            [
                DocgenEventsWarning(
                    f"{PATH}:5: cannot statically resolve event name"
                    f" for `logger.bind(...).info(...)`; skipping."
                    " Consider annotating the call site with a"
                    " `# docgen: event=<name>` comment so the catalogue"
                    " can still pick it up."
                ),
            ],
            id="dynamic-event-name-in-chain-describes-chain",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger()
logger.info("evt", x=1)
""",
            [
                EventEntry(
                    name="evt",
                    level="info",
                    attributes=frozenset({"x"}),
                    locations=[SourceLocation(path=PATH, line=4)],
                ),
            ],
            [],
            id="structlog-get_logger-no-args-produces-domainless-entry",
        ),
        pytest.param(
            """\
import structlog

log = unknown.bind(x=1)
log.info("evt")
""",
            [],
            [],
            id="bind-on-untracked-name-ignored",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("code_references")
logger.unbind("x").info("evt", y=1)
""",
            [],
            [],
            id="chain-with-non-bind-attr-ignored",
        ),
        pytest.param(
            """\
import structlog

unknown.bind(a=1).info("evt")
""",
            [],
            [],
            id="chain-bind-on-untracked-ignored",
        ),
        pytest.param(
            """\
import structlog

loggers = {}
loggers["x"].info("evt")
""",
            [],
            [],
            id="subscript-target-ignored",
        ),
        pytest.param(
            """\
import structlog

print("not a logger call")
""",
            [],
            [],
            id="bare-function-call-ignored",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("code_references")
logger.info()
""",
            [],
            [],
            id="emit-without-event-name-ignored",
        ),
        pytest.param(
            """\
import structlog

logger, spare = structlog.get_logger("a"), structlog.get_logger("b")
logger.info("scan.created")
""",
            [],
            [],
            id="tuple-destructuring-ignored",
        ),
        pytest.param(
            """\
import structlog

logger = unrelated()
logger.info("scan.created")
""",
            [],
            [],
            id="assignment-from-non-attribute-call-ignored",
        ),
        pytest.param(
            """\
import structlog

logger = factory.get_logger("code_references")
logger.info("scan.created")
""",
            [],
            [],
            id="get_logger-on-non-structlog-ignored",
        ),
        pytest.param(
            """\
import logging

logger = logging.getLogger("code_references")
logger.info("scan.created", extra={"organisation": 1})
""",
            [],
            [],
            id="stdlib-logging-getLogger-ignored",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("code_references")
logger.bind_or_whatever("not.an.event")
""",
            [],
            [],
            id="non-level-method-is-ignored-silently",
        ),
        pytest.param(
            """\
import structlog

domain = "sneaky"
logger = structlog.get_logger(domain)
logger.info("something.happened")
""",
            [],
            [
                DocgenEventsWarning(
                    f"{PATH}:4: cannot statically resolve logger domain"
                    f" for `logger`; skipping its events."
                ),
            ],
            id="non-resolvable-domain-warns-and-skips",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("code_references")
event_name = "scan." + "created"
logger.info(event_name)
""",
            [],
            [
                DocgenEventsWarning(
                    f"{PATH}:5: cannot statically resolve event name"
                    f" for `logger.info(...)`; skipping."
                    " Consider annotating the call site with a"
                    " `# docgen: event=<name>` comment so the catalogue"
                    " can still pick it up."
                ),
            ],
            id="dynamic-event-name-warns-and-skips",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("projects")


class ProjectWorker:
    organisation_id: str

    def logger(self, project_id: str) -> structlog.BoundLogger:
        return logger.bind(
            organisation__id=self.organisation_id,
            project__id=project_id,
        )

    def do_work(self, project_id: str) -> None:
        self.logger(project_id=project_id).info("project.worked")
""",
            [
                EventEntry(
                    name="projects.project.worked",
                    level="info",
                    attributes=frozenset({"organisation.id", "project.id"}),
                    locations=[SourceLocation(path=PATH, line=16)],
                ),
            ],
            [],
            id="self-method-accessor-resolves-via-class-scope",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("projects")


class BaseWorker:
    organisation_id: str

    def logger(self, project_id: str) -> structlog.BoundLogger:
        return logger.bind(
            organisation__id=self.organisation_id,
            project__id=project_id,
        )


class ProjectWorker(BaseWorker):
    def do_work(self, project_id: str) -> None:
        self.logger(project_id=project_id).info("project.worked")
""",
            [
                EventEntry(
                    name="projects.project.worked",
                    level="info",
                    attributes=frozenset({"organisation.id", "project.id"}),
                    locations=[SourceLocation(path=PATH, line=18)],
                ),
            ],
            [],
            id="self-method-accessor-inherited-from-same-file-parent",
        ),
        pytest.param(
            """\
import structlog


class Worker:
    def do_work(self) -> None:
        self.logger.info("project.worked")
        self.logger_factory().info("project.factoried")
""",
            [],
            [
                DocgenEventsWarning(
                    f"{PATH}:6: cannot resolve `self.logger.info(...)`:"
                    " `logger` isn't a tracked accessor on this class or any"
                    " same-file parent. Consider inlining the bind at the"
                    " call site or moving the accessor into this file."
                ),
                DocgenEventsWarning(
                    f"{PATH}:7: cannot resolve"
                    " `self.logger_factory(...).info(...)`:"
                    " `logger_factory` isn't a tracked accessor on this class"
                    " or any same-file parent. Consider inlining the bind at"
                    " the call site or moving the accessor into this file."
                ),
            ],
            id="unresolvable-self-emit-warns-and-skips",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("projects")


class ProjectWorker:
    @classmethod
    def logger(cls, project_id: str) -> structlog.BoundLogger:
        return logger.bind(project__id=project_id)

    @classmethod
    def do_work(cls, project_id: str) -> None:
        cls.logger(project_id=project_id).info("project.worked")
""",
            [
                EventEntry(
                    name="projects.project.worked",
                    level="info",
                    attributes=frozenset({"project.id"}),
                    locations=[SourceLocation(path=PATH, line=13)],
                ),
            ],
            [],
            id="cls-method-accessor-resolves-via-class-scope",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("projects")


class ProjectWorker:
    @property
    def logger(self) -> structlog.BoundLogger:
        \"\"\"Accessor with a docstring.\"\"\"
        return logger.bind(worker="project")

    def do_work(self) -> None:
        self.logger.info("project.worked")
""",
            [
                EventEntry(
                    name="projects.project.worked",
                    level="info",
                    attributes=frozenset({"worker"}),
                    locations=[SourceLocation(path=PATH, line=13)],
                ),
            ],
            [],
            id="property-accessor-with-docstring-resolves-via-class-scope",
        ),
        pytest.param(
            """\
import structlog

foo.bar.info("evt")
""",
            [],
            [],
            id="non-self-attribute-chain-ignored",
        ),
        pytest.param(
            """\
import structlog

some_factory().info("evt")
""",
            [],
            [],
            id="non-attribute-func-target-ignored",
        ),
        pytest.param(
            """\
import structlog

logger = structlog.get_logger("projects")


class Mixin:
    def logger(self) -> structlog.BoundLogger:
        return logger.bind(from_mixin=1)


class ProjectWorker(UnknownExternalBase, Mixin):
    def do_work(self) -> None:
        self.logger().info("project.worked")
""",
            [
                EventEntry(
                    name="projects.project.worked",
                    level="info",
                    attributes=frozenset({"from_mixin"}),
                    locations=[SourceLocation(path=PATH, line=13)],
                ),
            ],
            [],
            id="multiple-bases-skip-unknown-and-inherit-from-known",
        ),
    ],
)
def test_get_event_entries_from_source__emit_log__expected_entries(
    source: str,
    expected_entries: list[EventEntry],
    expected_warnings: list[DocgenEventsWarning],
) -> None:
    # Given / When
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always", DocgenEventsWarning)
        entries = list(
            get_event_entries_from_source(
                source,
                module_dotted=MODULE_DOTTED,
                path=PATH,
            )
        )

    # Then
    assert entries == expected_entries
    assert [(w.category, str(w.message)) for w in recorded] == [
        (type(expected), str(expected)) for expected in expected_warnings
    ]


OTHER_PATH = Path("projects/other.py")


@pytest.mark.parametrize(
    "entries, expected_merged, expected_warnings",
    [
        pytest.param(
            [
                EventEntry(
                    name="code_references.scan.created",
                    level="info",
                    attributes=frozenset({"organisation.id"}),
                    locations=[SourceLocation(path=PATH, line=10)],
                ),
                EventEntry(
                    name="code_references.scan.created",
                    level="info",
                    attributes=frozenset({"code_references.count"}),
                    locations=[SourceLocation(path=OTHER_PATH, line=20)],
                ),
            ],
            [
                EventEntry(
                    name="code_references.scan.created",
                    level="info",
                    attributes=frozenset({"organisation.id", "code_references.count"}),
                    locations=[
                        SourceLocation(path=PATH, line=10),
                        SourceLocation(path=OTHER_PATH, line=20),
                    ],
                ),
            ],
            [],
            id="same-event-two-sites-collapses-with-union-attrs",
        ),
        pytest.param(
            [
                EventEntry(
                    name="code_references.scan.created",
                    level="info",
                    attributes=frozenset({"organisation.id"}),
                    locations=[SourceLocation(path=PATH, line=10)],
                ),
                EventEntry(
                    name="code_references.scan.created",
                    level="info",
                    attributes=frozenset({"organisation.id"}),
                    locations=[SourceLocation(path=PATH, line=10)],
                ),
            ],
            [
                EventEntry(
                    name="code_references.scan.created",
                    level="info",
                    attributes=frozenset({"organisation.id"}),
                    locations=[SourceLocation(path=PATH, line=10)],
                ),
            ],
            [],
            id="identical-locations-deduped",
        ),
        pytest.param(
            [
                EventEntry(
                    name="code_references.scan.created",
                    level="info",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=10)],
                ),
                EventEntry(
                    name="code_references.scan.created",
                    level="debug",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=OTHER_PATH, line=20)],
                ),
            ],
            [
                EventEntry(
                    name="code_references.scan.created",
                    level="info",
                    attributes=frozenset(),
                    locations=[
                        SourceLocation(path=PATH, line=10),
                        SourceLocation(path=OTHER_PATH, line=20),
                    ],
                ),
            ],
            [
                DocgenEventsWarning(
                    "`code_references.scan.created` is emitted at diverging"
                    f" log levels: `info` at {PATH}:10,"
                    f" `debug` at {OTHER_PATH}:20."
                    " Keeping first-seen level `info`; reconcile the emission"
                    " sites to silence this warning."
                ),
            ],
            id="diverging-level-warns-and-first-wins",
        ),
        pytest.param(
            [
                EventEntry(
                    name="zulu",
                    level="info",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=3)],
                ),
                EventEntry(
                    name="alpha",
                    level="info",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=1)],
                ),
                EventEntry(
                    name="mike",
                    level="info",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=2)],
                ),
            ],
            [
                EventEntry(
                    name="alpha",
                    level="info",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=1)],
                ),
                EventEntry(
                    name="mike",
                    level="info",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=2)],
                ),
                EventEntry(
                    name="zulu",
                    level="info",
                    attributes=frozenset(),
                    locations=[SourceLocation(path=PATH, line=3)],
                ),
            ],
            [],
            id="output-sorted-alphabetically-by-event-name",
        ),
    ],
)
def test_merge_event_entries__various_entries__expected_merged_and_warnings(
    entries: list[EventEntry],
    expected_merged: list[EventEntry],
    expected_warnings: list[DocgenEventsWarning],
) -> None:
    # Given / When
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always", DocgenEventsWarning)
        merged = merge_event_entries(entries)

    # Then
    assert merged == expected_merged
    assert [(w.category, str(w.message)) for w in recorded] == [
        (type(expected), str(expected)) for expected in expected_warnings
    ]


ROOT = Path("/fake/myapp")


@pytest.mark.parametrize(
    "tree, app_label, expected_entries",
    [
        pytest.param(
            {
                "views.py": """\
import structlog
logger = structlog.get_logger("myapp")
logger.info("viewed")
""",
                "nested/models.py": """\
import structlog
logger = structlog.get_logger("myapp")
logger.info("modeled")
""",
            },
            "myapp",
            [
                EventEntry(
                    name="myapp.modeled",
                    level=ANY,
                    attributes=ANY,
                    locations=[
                        SourceLocation(path=ROOT / "nested/models.py", line=3),
                    ],
                ),
                EventEntry(
                    name="myapp.viewed",
                    level=ANY,
                    attributes=ANY,
                    locations=[SourceLocation(path=ROOT / "views.py", line=3)],
                ),
            ],
            id="walks-all-py-files-across-subdirs",
        ),
        pytest.param(
            {
                "views.py": """\
import structlog
logger = structlog.get_logger("myapp")
logger.info("included")
""",
                "migrations/0001_initial.py": """\
import structlog
logger = structlog.get_logger("myapp")
logger.info("from_migration")
""",
                "tests/test_views.py": """\
import structlog
logger = structlog.get_logger("myapp")
logger.info("from_test_subdir")
""",
                "conftest.py": """\
import structlog
logger = structlog.get_logger("myapp")
logger.info("from_conftest")
""",
                "test_thing.py": """\
import structlog
logger = structlog.get_logger("myapp")
logger.info("from_test_module")
""",
            },
            "myapp",
            [
                EventEntry(
                    name="myapp.included",
                    level=ANY,
                    attributes=ANY,
                    locations=[SourceLocation(path=ROOT / "views.py", line=3)],
                ),
            ],
            id="skips-migrations-tests-conftest-test-modules",
        ),
        pytest.param(
            {
                "views.py": """\
import structlog
logger = structlog.get_logger("myapp")
logger.info("viewed")
""",
                "management/commands/do_thing.py": """\
import structlog
logger = structlog.get_logger("myapp")
logger.info("from_command")
""",
            },
            "myapp",
            [
                EventEntry(
                    name="myapp.viewed",
                    level=ANY,
                    attributes=ANY,
                    locations=[SourceLocation(path=ROOT / "views.py", line=3)],
                ),
            ],
            id="skips-management-commands-by-default",
        ),
        pytest.param(
            {
                "views.py": """\
import structlog
logger = structlog.get_logger("task_processor")
logger.info("setup")
""",
                "management/commands/run_processor.py": """\
import structlog
logger = structlog.get_logger("task_processor")
logger.info("task.dispatched")
""",
            },
            "task_processor",
            [
                EventEntry(
                    name="task_processor.setup",
                    level=ANY,
                    attributes=ANY,
                    locations=[SourceLocation(path=ROOT / "views.py", line=3)],
                ),
                EventEntry(
                    name="task_processor.task.dispatched",
                    level=ANY,
                    attributes=ANY,
                    locations=[
                        SourceLocation(
                            path=ROOT / "management/commands/run_processor.py",
                            line=3,
                        ),
                    ],
                ),
            ],
            id="includes-management-commands-for-task-processor-app",
        ),
    ],
)
def test_get_event_entries_from_tree__various_trees__expected_entries(
    fs: FakeFilesystem,
    tree: dict[str, str],
    app_label: str,
    expected_entries: list[EventEntry],
) -> None:
    # Given
    for relative, source in tree.items():
        fs.create_file(str(ROOT / relative), contents=source)

    # When
    entries = sorted(
        get_event_entries_from_tree(ROOT, app_label=app_label, module_prefix=app_label),
        key=lambda e: e.name,
    )

    # Then
    assert entries == expected_entries
