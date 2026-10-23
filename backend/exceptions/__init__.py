"""Custom exception classes, so the API can turn each kind of failure into a clear HTTP answer.
    LLMNotConfiguredException -> 400 Bad Request
    IngestionException -> 500 Internal Server Error
"""

class ProcurementPilotAIException(Exception):
    """Base class for all exceptions in the Procurement Pilot AI project."""

class LLMNotConfiguredException(ProcurementPilotAIException):
    """Exception raised when the LLM is not configured properly."""

class IngestionException(ProcurementPilotAIException):
    """Exception raised when there is an error during the ingestion process."""