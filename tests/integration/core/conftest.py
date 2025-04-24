from typing import Generator

import pytest
from pytest_httpserver import HTTPServer


@pytest.fixture()
def http_server(unused_tcp_port: int) -> Generator[HTTPServer, None, None]:
    with HTTPServer(port=unused_tcp_port) as server:
        yield server
