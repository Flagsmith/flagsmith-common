from datetime import datetime


class TaskProcessingError(Exception):
    pass


class InvalidArgumentsError(TaskProcessingError):
    pass


class TaskBackoffError(TaskProcessingError):
    """
    Raise this exception inside a task to indicate that it should be retried after a delay.
    This is typically used when a task fails due to a temporary issue, such as
    a network error or a service being unavailable.
    """

    def __init__(
        self,
        delay_until: datetime | None = None,
    ) -> None:
        super().__init__()
        self.delay_until = delay_until


class TaskQueueFullError(Exception):
    pass
