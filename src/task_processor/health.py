import uuid

import backoff
from health_check.backends import BaseHealthCheckBackend  # type: ignore[import-untyped]
from health_check.exceptions import HealthCheckException  # type: ignore[import-untyped]

from task_processor.models import HealthCheckModel
from task_processor.tasks import create_health_check_model


def is_processor_healthy(max_tries: int = 5, factor: float = 0.1) -> bool:
    health_check_model_uuid = str(uuid.uuid4())

    create_health_check_model.delay(args=(health_check_model_uuid,))

    @backoff.on_predicate(
        backoff.expo,
        lambda m: m is None,
        max_tries=max_tries,
        factor=factor,
        jitter=None,
    )
    def get_health_check_model() -> HealthCheckModel | None:
        return HealthCheckModel.objects.filter(uuid=health_check_model_uuid).first()

    health_check_model = get_health_check_model()
    if health_check_model:
        health_check_model.delete()
        return True

    return False


class TaskProcessorHealthCheckBackend(BaseHealthCheckBackend):  # type: ignore[misc]
    #: The status endpoints will respond with a 200 status code
    #: even if the check errors.
    critical_service = False

    def check_status(self) -> None:
        if not is_processor_healthy():
            raise HealthCheckException("Task processor is unable to process tasks.")

    def identifier(self) -> str:
        return self.__class__.__name__  # Display name on the endpoint.
