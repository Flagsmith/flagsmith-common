from typing import Literal

DEFAULT_PROMETHEUS_MULTIPROC_DIR_NAME = "flagsmith-prometheus"

LOGGING_DEFAULT_ROOT_LOG_LEVEL = "WARNING"

OtlpProtocol = Literal["grpc", "http/protobuf"]
DEFAULT_OTLP_PROTOCOL: OtlpProtocol = "http/protobuf"
