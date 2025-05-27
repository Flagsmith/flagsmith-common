import argparse
import socket
import urllib.parse

import requests

DEFAULT_PORT = 8000
DEFAULT_TIMEOUT_SECONDS = 1


def get_args(
    argv: list[str],
    *,
    prog: str,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Perform health checks. "
            f"If ran without subcommand, defaults to a TCP check of port {DEFAULT_PORT}."
        ),
        prog=prog,
    )
    subcommands = parser.add_subparsers(dest="subcommand")
    tcp_parser = subcommands.add_parser(
        "tcp",
        help="Check if the API is able to accept local TCP connections",
    )
    tcp_parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to check the API on (default: {DEFAULT_PORT})",
    )
    tcp_parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Socket timeout for the connection attempt in seconds (default: {DEFAULT_TIMEOUT_SECONDS})",
    )
    http_parser = subcommands.add_parser(
        "http", help="Check if the API is able to serve HTTP requests"
    )
    http_parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port to check the API on (default: {DEFAULT_PORT})",
    )
    http_parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS})",
    )
    http_parser.add_argument(
        "path",
        nargs="?",
        type=str,
        default="/health/liveness",
        help="Request path (default: /health/liveness)",
    )
    return parser.parse_args(argv)


def check_tcp_connection(
    port: int,
    timeout_seconds: int,
) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_seconds)
    try:
        sock.connect(("127.0.0.1", port))
    except socket.error as e:
        print(f"Failed: {e} {port=}")
        exit(1)
    else:
        exit(0)
    finally:
        sock.close()


def check_http_response(
    port: int,
    timeout_seconds: int,
    path: str,
) -> None:
    url = urllib.parse.urljoin(f"http://127.0.0.1:{port}", path)
    requests.get(
        url,
        timeout=timeout_seconds,
    ).raise_for_status()


def main(
    argv: list[str],
    *,
    prog: str,
) -> None:
    args = get_args(argv, prog=prog)
    match args.subcommand:
        case None:
            check_tcp_connection(
                port=DEFAULT_PORT,
                timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
            )
        case "tcp":
            check_tcp_connection(
                port=args.port,
                timeout_seconds=args.timeout,
            )
        case "http":
            check_http_response(
                port=args.port,
                timeout_seconds=args.timeout,
                path=args.path,
            )
