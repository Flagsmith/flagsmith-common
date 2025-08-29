import enum
import json
import logging
import pathlib
import random
from functools import lru_cache
from itertools import cycle
from typing import Iterator, NotRequired, TypedDict, TypeVar

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import connections
from django.db.models import Manager, Model
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)

UNKNOWN = "unknown"
VERSIONS_INFO_FILE_LOCATION = ".versions.json"

ModelType = TypeVar("ModelType", bound=Model)

_sequential_replica_manager: dict[str, Iterator[str]] = {}


class ReplicaReadStrategy(enum.StrEnum):
    DISTRIBUTED = enum.auto()
    SEQUENTIAL = enum.auto()


class SelfHostedData(TypedDict):
    has_users: bool
    has_logins: bool


VersionManifest = TypedDict(
    "VersionManifest",
    {
        ".": str,  # This key is used to store the version of the package itself
    },
)


class VersionInfo(TypedDict):
    ci_commit_sha: str
    image_tag: str
    has_email_provider: bool
    is_enterprise: bool
    is_saas: bool
    self_hosted_data: SelfHostedData | None
    package_versions: NotRequired[VersionManifest]


@lru_cache()
def is_enterprise() -> bool:
    return pathlib.Path("./ENTERPRISE_VERSION").exists()


@lru_cache()
def is_saas() -> bool:
    return pathlib.Path("./SAAS_DEPLOYMENT").exists()


def is_oss() -> bool:
    return not (is_enterprise() or is_saas())


@lru_cache()
def has_email_provider() -> bool:
    match settings.EMAIL_BACKEND:
        case "django.core.mail.backends.smtp.EmailBackend":
            return settings.EMAIL_HOST_USER is not None
        case "sgbackend.SendGridBackend":
            return settings.SENDGRID_API_KEY is not None
        case "django_ses.SESBackend":
            return settings.AWS_SES_REGION_ENDPOINT is not None
        case _:
            return False


def get_version_info() -> VersionInfo:
    """Returns the version information for the current deployment"""
    _is_saas = is_saas()
    version_json: VersionInfo = {
        "ci_commit_sha": get_file_contents("./CI_COMMIT_SHA") or UNKNOWN,
        "image_tag": UNKNOWN,
        "has_email_provider": has_email_provider(),
        "is_enterprise": is_enterprise(),
        "is_saas": _is_saas,
        "self_hosted_data": None,
    }

    manifest_versions = get_versions_from_manifest()
    version_json["package_versions"] = manifest_versions
    version_json["image_tag"] = manifest_versions["."]

    if not _is_saas:
        user_objects: Manager[AbstractBaseUser] = getattr(get_user_model(), "objects")

        version_json["self_hosted_data"] = {
            "has_users": user_objects.exists(),
            "has_logins": user_objects.filter(last_login__isnull=False).exists(),
        }

    return version_json


def get_version() -> str:
    """Return the version number of the current deployment"""
    manifest_versions = get_versions_from_manifest()
    return manifest_versions.get(".", UNKNOWN)


@lru_cache()
def get_versions_from_manifest() -> VersionManifest:
    """Read the version info from the manifest file"""
    raw_content = get_file_contents(VERSIONS_INFO_FILE_LOCATION)
    if not raw_content:
        return {".": UNKNOWN}

    manifest: VersionManifest = json.loads(raw_content)
    return manifest


@lru_cache()
def get_file_contents(file_path: str) -> str | None:
    """Attempts to read a file from the filesystem and return the contents"""
    try:
        with open(file_path) as f:
            return f.read().replace("\n", "")
    except FileNotFoundError:
        return None


def using_database_replica(
    manager: Manager[ModelType],
    replica_prefix: str = "replica_",
) -> Manager[ModelType]:
    """Attempts to bind a manager to a healthy database replica"""
    local_replicas = [name for name in connections if name.startswith(replica_prefix)]

    if not local_replicas:
        logger.info("No replicas set up.")
        return manager

    chosen_replica = None

    if settings.REPLICA_READ_STRATEGY == ReplicaReadStrategy.SEQUENTIAL:
        _sequential_replica_manager.setdefault(replica_prefix, cycle(local_replicas))
        for _ in range(len(local_replicas)):
            attempted_replica = next(_sequential_replica_manager[replica_prefix])
            try:
                connections[attempted_replica].ensure_connection()
                chosen_replica = attempted_replica
                break
            except OperationalError:
                logger.warning(f"Replica '{attempted_replica}' is not available.")
                continue

    if settings.REPLICA_READ_STRATEGY == ReplicaReadStrategy.DISTRIBUTED:
        for _ in range(len(local_replicas)):
            attempted_replica = random.choice(local_replicas)
            try:
                connections[attempted_replica].ensure_connection()
                chosen_replica = attempted_replica
                break
            except OperationalError:
                logger.warning(f"Replica '{attempted_replica}' is not available.")
                local_replicas.remove(attempted_replica)
                continue

    if not chosen_replica:
        if replica_prefix == "replica_":
            logger.warning("Falling back to cross-region replicas, if any.")
            return using_database_replica(manager, "cross_region_replica_")
        raise OperationalError("No available replicas")

    return manager.db_manager(chosen_replica)
