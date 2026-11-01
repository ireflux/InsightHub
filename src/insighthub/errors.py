from typing import Optional


class InsightHubError(Exception):
    retryable: bool = False

    def __init__(self, message: str):
        super().__init__(message)


class RetryableInsightHubError(InsightHubError):
    retryable = True


class NonRetryableInsightHubError(InsightHubError):
    retryable = False


class SourceFetchError(RetryableInsightHubError):
    pass


class LLMProcessingError(RetryableInsightHubError):
    pass


class RateLimitError(LLMProcessingError):
    """Provider rejected a request because a request-rate quota was exceeded."""

    def __init__(self, message: str, retry_after_seconds: Optional[float] = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class SinkDeliveryError(RetryableInsightHubError):
    pass


class ConfigValidationError(NonRetryableInsightHubError):
    pass


class PromptRenderingError(NonRetryableInsightHubError):
    pass
