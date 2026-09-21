"""Safe boto3 CloudWatch client construction.

Collection stays disabled when ``AWS_ENABLED=false``. Credentials are taken
from the environment (or IAM role when deployed on AWS) and are never logged.
"""

from typing import Any

import boto3

from monitoring.cloudwatch.models import CloudWatchDisabledError


def build_client(config) -> Any:
    """Create a boto3 CloudWatch client from configuration.

    Args:
        config: A :class:`CloudWatchConfig`.

    Raises:
        CloudWatchDisabledError: If collection is disabled.
    """
    if not config.aws_enabled:
        raise CloudWatchDisabledError(
            "CloudWatch integration is disabled (AWS_ENABLED=false)"
        )

    kwargs: dict[str, Any] = {}
    if config.aws_region:
        kwargs["region_name"] = config.aws_region
    if config.aws_access_key_id and config.aws_secret_access_key:
        kwargs["aws_access_key_id"] = config.aws_access_key_id
        kwargs["aws_secret_access_key"] = config.aws_secret_access_key
    if config.aws_session_token:
        kwargs["aws_session_token"] = config.aws_session_token
    return boto3.client("cloudwatch", **kwargs)