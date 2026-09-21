"""Metric collection from live sources into MetricRecords.

Collectors are modular and swappable: the Prometheus collector speaks only
HTTP to a Prometheus server, and the CloudWatch collector delegates to
:class:`CloudWatchService` (boto3 stays behind that boundary).
"""