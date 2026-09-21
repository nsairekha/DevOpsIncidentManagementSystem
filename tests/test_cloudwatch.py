"""Tests for the AWS CloudWatch metrics client (API calls mocked with Stubber)."""

from datetime import datetime, timezone

import pandas as pd
import pytest
from botocore.stub import Stubber

from backend.app.config import Settings
from monitoring import (
    ALLOWED_STATISTICS,
    CloudWatchClient,
    CloudWatchMetric,
    cloudwatch_client_from_settings,
    metrics_to_dataframe,
)

T0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 1, 1, 12, 5, tzinfo=timezone.utc)
T2 = datetime(2026, 1, 1, 12, 10, tzinfo=timezone.utc)


def make_stubbed_client():
    """CloudWatchClient whose underlying boto3 client is stubbed."""
    client = CloudWatchClient(
        region_name="us-east-1",
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret",
    )
    stubber = Stubber(client.client)
    return client, stubber


def test_fetch_and_normalize_metric_statistics() -> None:
    """Datapoints are fetched and normalised into CloudWatchMetric objects."""
    client, stubber = make_stubbed_client()

    expected_params = {
        "Namespace": "AWS/EC2",
        "MetricName": "CPUUtilization",
        "Dimensions": [{"Name": "InstanceId", "Value": "i-123456"}],
        "StartTime": T0,
        "EndTime": T2,
        "Period": 300,
        "Statistics": ["Average"],
    }
    response = {
        "Datapoints": [
            {"Timestamp": T2, "Average": 92.4, "Unit": "Percent"},
            {"Timestamp": T0, "Average": 12.5, "Unit": "Percent"},
            {"Timestamp": T1, "Average": 45.0, "Unit": "Percent"},
        ]
    }
    stubber.add_response("get_metric_statistics", response, expected_params)
    stubber.activate()

    metrics = client.get_metric_statistics(
        namespace="AWS/EC2",
        metric_name="CPUUtilization",
        dimensions={"InstanceId": "i-123456"},
        start_time=T0,
        end_time=T2,
        period=300,
    )

    stubber.assert_no_pending_responses()

    # Chronologically sorted, normalised, and annotated with metadata.
    assert [m.timestamp for m in metrics] == [T0, T1, T2]
    assert [m.value for m in metrics] == [12.5, 45.0, 92.4]
    assert metrics[0].namespace == "AWS/EC2"
    assert metrics[0].metric_name == "CPUUtilization"
    assert metrics[0].unit == "Percent"
    assert metrics[0].dimensions == (("InstanceId", "i-123456"),)


def test_empty_datapoints_return_empty_list() -> None:
    """No datapoints yields an empty list rather than an error."""
    client, stubber = make_stubbed_client()
    stubber.add_response("get_metric_statistics", {"Datapoints": []})
    stubber.activate()

    metrics = client.get_metric_statistics(
        namespace="AWS/SQS",
        metric_name="ApproximateNumberOfMessagesVisible",
        dimensions={"QueueName": "q"},
        start_time=T0,
        end_time=T1,
        period=60,
    )

    stubber.assert_no_pending_responses()
    assert metrics == []


def test_invalid_statistic_raises() -> None:
    """Unsupported statistics are rejected before any API call."""
    client, _ = make_stubbed_client()

    with pytest.raises(ValueError, match="unsupported statistic"):
        client.get_metric_statistics(
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={},
            start_time=T0,
            end_time=T1,
            period=300,
            statistic="Median",
        )


def test_allowed_statistics_set() -> None:
    """The permitted CloudWatch statistics are exposed."""
    assert ALLOWED_STATISTICS == {"Average", "Sum", "Minimum", "Maximum", "SampleCount"}


def test_metrics_to_dataframe() -> None:
    """Normalised metrics convert to a tidy DataFrame."""
    metrics = [
        CloudWatchMetric("AWS/EC2", "CPUUtilization", T0, 12.5, "Percent", (("InstanceId", "i-1"),)),
        CloudWatchMetric("AWS/EC2", "CPUUtilization", T1, 45.0, "Percent", (("InstanceId", "i-1"),)),
    ]

    df = metrics_to_dataframe(metrics)

    assert list(df.columns) == ["timestamp", "metric", "value", "unit", "InstanceId"]
    assert df["metric"].tolist() == ["AWS/EC2/CPUUtilization", "AWS/EC2/CPUUtilization"]
    assert df["value"].tolist() == [12.5, 45.0]
    assert df["InstanceId"].tolist() == ["i-1", "i-1"]


def test_metrics_to_dataframe_empty() -> None:
    """An empty list yields a DataFrame with the expected columns."""
    df = metrics_to_dataframe([])
    assert df.empty
    assert list(df.columns) == ["timestamp", "metric", "value", "unit"]


def test_client_from_settings(monkeypatch) -> None:
    """Env vars flow through settings into the CloudWatch client session."""
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "ak-test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "sk-test")

    settings = Settings()
    client = cloudwatch_client_from_settings(settings)

    assert client.session.region_name == "eu-west-1"
    creds = client.session.get_credentials()
    assert creds is not None
    assert creds.access_key == "ak-test"
    assert creds.secret_key == "sk-test"


def test_dataframe_baseline_integration() -> None:
    """Normalised CloudWatch data feeds directly into baseline computation."""
    from dataset import compute_baselines

    metrics = [
        CloudWatchMetric("AWS/EC2", "CPUUtilization", T0, 10.0, "Percent", ()),
        CloudWatchMetric("AWS/EC2", "CPUUtilization", T1, 20.0, "Percent", ()),
        CloudWatchMetric("AWS/EC2", "CPUUtilization", T2, 30.0, "Percent", ()),
    ]
    df = metrics_to_dataframe(metrics)

    baselines = compute_baselines(df, columns=["value"])

    assert baselines["value"].mean == pytest.approx(20.0)