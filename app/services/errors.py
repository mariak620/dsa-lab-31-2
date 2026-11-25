class ServiceError(Exception):
    code = "INTERNAL_ERROR"


class NotFound(ServiceError):
    code = "NOT_FOUND"


class TransitionNotAllowed(ServiceError):
    code = "TRANSITION_NOT_ALLOWED"


class OrderValidationError(ServiceError):
    code = "VALIDATION_ERROR"