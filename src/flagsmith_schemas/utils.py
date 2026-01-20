import gzip
import typing

import simplejson as json


def json_gzip(value: typing.Any) -> bytes:
    return gzip.compress(
        json.dumps(
            value,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
        mtime=0,
    )
