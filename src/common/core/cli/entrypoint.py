"""
The `flagsmith` console script entry point.

This module is intentionally kept lightweight: it must not import Django or any
other heavy dependencies at module level.

Health checks are commonly run at a high frequency, e.g. every few seconds by a
Docker `HEALTHCHECK` instruction, so they bypass the full CLI environment set up
by `common.core.main` to keep their CPU footprint minimal.

All other commands are delegated to `common.core.main.main`.
"""

import os
import sys

HEALTHCHECK_SUBCOMMANDS = frozenset(
    {
        "healthcheck",
        # Backwards compatibility for task-processor health checks
        # See https://github.com/Flagsmith/flagsmith-task-processor/issues/24
        "checktaskprocessorthreadhealth",
    }
)


def main(argv: list[str] = sys.argv) -> None:
    if len(argv) > 1 and argv[1] in HEALTHCHECK_SUBCOMMANDS:
        from common.core.cli import healthcheck

        return healthcheck.main(
            argv[2:],
            prog=f"{os.path.basename(argv[0])} {argv[1]}",
        )

    from common.core.main import main as full_main

    return full_main(argv)
