"""
Note: django doesn't support adding submodules to the migrations module directory
that don't include a Migration class. As such, I've defined this helpers submodule
and simplified the imports by defining the __all__ attribute.
"""

from common.migrations.helpers.postgres_helpers import PostgresOnlyRunSQL

__all__ = ["PostgresOnlyRunSQL"]
