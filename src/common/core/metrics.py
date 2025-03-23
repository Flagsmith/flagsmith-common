import prometheus_client

from common.core.utils import get_version_info
from common.prometheus.constants import UNKNOWN_LABEL_VALUE

flagsmith_build_info = prometheus_client.Gauge(
    "flagsmith_build_info",
    "Flagsmith version and build information",
    ["ci_commit_sha", "version"],
    multiprocess_mode="max",
)


def advertise() -> None:
    # Advertise Flagsmith build info.
    version_info = get_version_info()
    flagsmith_build_info.labels(
        ci_commit_sha=version_info["ci_commit_sha"],
        version=version_info.get("package_versions", {}).get(".")
        or UNKNOWN_LABEL_VALUE,
    ).set(1)


advertise()
