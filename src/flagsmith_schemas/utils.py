import gzip
import typing

import simplejson as json

if typing.TYPE_CHECKING:
    from flagsmith_schemas.types import JsonGzipped

T = typing.TypeVar("T")


def json_gzip(value: T) -> "JsonGzipped[T]":
    return typing.cast(
        "JsonGzipped[T]",
        gzip.compress(
            json.dumps(
                value,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8"),
            mtime=0,
        ),
    )
