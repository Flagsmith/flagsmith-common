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

from common.core.cli import healthcheck


def main(argv: list[str] = sys.argv) -> None:
    if len(argv) > 1 and argv[1] in healthcheck.SUBCOMMANDS:
        return healthcheck.main(
            argv[2:],
            prog=f"{os.path.basename(argv[0])} {argv[1]}",
        )

    from common.core.main import main as full_main

    return full_main(argv)
