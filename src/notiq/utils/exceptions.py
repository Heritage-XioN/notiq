class NotiqException(Exception):
    """
    Base exception for all notiq exceptions.
    """


class TaskNameRequiredError(NotiqException):
    """
    Raised when a task name is required but not provided.
    """


class SchedulerValidationError(NotiqException):
    """
    Raised when scheduler configuration parameters are invalid or missing.
    """
