import argparse
import socket


def get_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check if the API is able to accept local TCP connections.",
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port to check the API on (default: 8000)",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=1,
        help="Socket timeout for the connection attempt in seconds (default: 1)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> None:
    args = get_args(argv)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(args.timeout)
    try:
        sock.connect(("127.0.0.1", args.port))
    except socket.error as e:
        print(f"Failed: {e} {args.port=}")
        exit(1)
    else:
        exit(0)
    finally:
        sock.close()
