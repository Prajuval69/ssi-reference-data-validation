"""Domain-specific exceptions with safe, actionable messages."""


class SSIValidationError(Exception):
    """Base exception for the project."""


class InputSchemaError(SSIValidationError):
    """Raised when an input dataset does not meet the required schema."""


class WorkflowError(SSIValidationError):
    """Raised when a workflow action violates a configured control."""


class PersistenceError(SSIValidationError):
    """Raised when persistence cannot complete safely."""

