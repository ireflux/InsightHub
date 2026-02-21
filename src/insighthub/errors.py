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


class SinkDeliveryError(RetryableInsightHubError):
    pass


class ConfigValidationError(NonRetryableInsightHubError):
    pass


class PromptRenderingError(NonRetryableInsightHubError):
    pass
