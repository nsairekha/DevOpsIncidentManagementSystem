"""CloudWatch configuration loaded purely from environment variables.

Supported variables (see ``.env.example``)::

    AWS_ENABLED=false
    AWS_REGION=
    AWS_ACCESS_KEY_ID=
    AWS_SECRET_ACCESS_KEY=
    AWS_SESSION_TOKEN=
    CLOUDWATCH_NAMESPACE=AWS/EC2
    CLOUDWATCH_DIMENSION_NAME=InstanceId
    CLOUDWATCH_DIMENSION_VALUE=
    CLOUDWATCH_LOOKBACK_MINUTES=10
    CLOUDWATCH_PERIOD=60

Secret values are never logged; this object is never printed to logs.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class CloudWatchConfig(BaseSettings):
    """Configuration for the CloudWatch integration."""

    aws_enabled: bool = False
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_session_token: str | None = None

    cloudwatch_namespace: str = "AWS/EC2"
    cloudwatch_dimension_name: str = "InstanceId"
    cloudwatch_dimension_value: str = ""
    cloudwatch_lookback_minutes: int = 10
    cloudwatch_period: int = 60

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def dimensions(self) -> dict[str, str]:
        """Configured resource dimensions (empty when no resource is set)."""
        if not self.cloudwatch_dimension_value:
            return {}
        return {self.cloudwatch_dimension_name: self.cloudwatch_dimension_value}