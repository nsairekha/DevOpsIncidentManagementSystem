"""CloudWatch status and metric endpoints (``/api/v1/cloudwatch``).

The endpoints never expose credentials. Without ``AWS_ENABLED=true`` they
report the integration as disabled; ``demo=true`` serves clearly-marked
``cloudwatch_demo`` records for pipeline testing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.schemas.cloudwatch import (
    CloudWatchMetricsResponse,
    CloudWatchStatusResponse,
)
from monitoring.cloudwatch.config import CloudWatchConfig
from monitoring.cloudwatch.models import (
    CloudWatchAWSError,
    CloudWatchConfigError,
    CloudWatchDisabledError,
)
from monitoring.cloudwatch.service import CloudWatchService

router = APIRouter(prefix="/api/v1/cloudwatch", tags=["cloudwatch"])


def get_cloudwatch_config() -> CloudWatchConfig:
    """Build configuration from the environment on every request."""
    return CloudWatchConfig()


@router.get("/status", response_model=CloudWatchStatusResponse, summary="CloudWatch status")
def cloudwatch_status(
    config: CloudWatchConfig = Depends(get_cloudwatch_config),
) -> CloudWatchStatusResponse:
    """Report whether CloudWatch collection is enabled and configured."""
    return CloudWatchStatusResponse(**CloudWatchService(config).status())


@router.get(
    "/metrics",
    response_model=CloudWatchMetricsResponse,
    summary="CloudWatch metrics (normalized)",
)
def cloudwatch_metrics(
    config: CloudWatchConfig = Depends(get_cloudwatch_config),
    metric_name: str = Query(default="CPUUtilization"),
    resource_id: str | None = Query(default=None),
    lookback_minutes: int | None = Query(default=None, gt=0),
    statistic: str = Query(default="Average"),
    demo: bool = Query(default=False),
) -> CloudWatchMetricsResponse:
    """Return normalized CloudWatch metric records for a resource/window."""
    service = CloudWatchService(config)
    try:
        records = service.get_metrics(
            metric_name=metric_name,
            resource_id=resource_id,
            lookback_minutes=lookback_minutes,
            statistic=statistic,
            demo=demo,
        )
    except CloudWatchDisabledError as exc:
        raise HTTPException(status_code=503, detail=exc.message) from exc
    except CloudWatchConfigError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    except CloudWatchAWSError as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc
    return CloudWatchMetricsResponse(count=len(records), records=records)