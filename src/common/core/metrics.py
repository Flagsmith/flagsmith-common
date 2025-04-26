import prometheus_client
from django.conf import settings

from common.core.utils import get_version_info

flagsmith_build_info = prometheus_client.Gauge(
    "flagsmith_build_info",
    "Flagsmith version and build information.",
    ["ci_commit_sha", "version"],
    multiprocess_mode="livemax",
)


def advertise() -> None:
    # Advertise Flagsmith build info.
    version_info = get_version_info()

    flagsmith_build_info.labels(
        ci_commit_sha=version_info["ci_commit_sha"],
        version=version_info.get("package_versions", {}).get(".") or "unknown",
    ).set(1)


if not settings.DOCGEN_MODE:
    advertise()
