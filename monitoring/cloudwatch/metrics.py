"""CloudWatch metric retrieval over a UTC lookback window.

Uses ``get_metric_statistics`` with a 60 s period by default. Every AWS-side
failure (credentials, permissions, region, network, API errors) is converted
to :class:`CloudWatchAWSError` with the AWS error code preserved — errors
are structured, never silently swallowed.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    NoRegionError,
)

from monitoring.cloudwatch.models import CloudWatchAWSError


def lookback_window(lookback_minutes: int) -> tuple[datetime, datetime]:
    """Return ``(start, end)`` in UTC covering the last ``lookback_minutes``.

    Raises:
        CloudWatchAWSError: If the lookback is not positive.
    """
    if lookback_minutes <= 0:
        raise CloudWatchAWSError(
            f"lookback_minutes must be positive, got {lookback_minutes}"
        )
    end = datetime.now(timezone.utc)
    return end - timedelta(minutes=lookback_minutes), end


def fetch_datapoints(
    client: Any,
    *,
    namespace: str,
    metric_name: str,
    dimensions: dict[str, str],
    start_time: datetime,
    end_time: datetime,
    period: int,
    statistics: list[str],
) -> list[dict]:
    """Fetch raw CloudWatch datapoints, oldest first (may be empty).

    Raises:
        CloudWatchAWSError: On any AWS-side failure, with ``aws_code`` set
            for service errors (e.g. ``AccessDenied``, ``InvalidParameter``).
    """
    try:
        response = client.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            Dimensions=[
                {"Name": name, "Value": value}
                for name, value in dimensions.items()
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=statistics,
        )
    except NoCredentialsError as exc:
        raise CloudWatchAWSError(
            "AWS credentials not found; configure AWS_ACCESS_KEY_ID / "
            "AWS_SECRET_ACCESS_KEY or an IAM role",
            aws_code="NoCredentials",
        ) from exc
    except NoRegionError as exc:
        raise CloudWatchAWSError(
            "AWS region not configured; set AWS_REGION",
            aws_code="NoRegion",
        ) from exc
    except EndpointConnectionError as exc:
        raise CloudWatchAWSError(
            f"cannot reach the CloudWatch endpoint: {exc}",
            aws_code="EndpointConnection",
        ) from exc
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        raise CloudWatchAWSError(
            f"CloudWatch API error ({code}): "
            f"{exc.response.get('Error', {}).get('Message', exc)}",
            aws_code=code,
        ) from exc
    except BotoCoreError as exc:
        raise CloudWatchAWSError(f"AWS SDK error: {exc}") from exc

    datapoints = response.get("Datapoints", [])
    return sorted(datapoints, key=lambda point: point["Timestamp"])