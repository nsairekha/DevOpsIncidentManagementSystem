"""Synchronous HTTP helper for service-to-service calls.

Calls carry the caller's ``X-Request-ID`` so a distributed trace keeps one ID
across services. Transport errors and timeouts are converted to
:class:`DownstreamError` so route handlers can respond without crashing.
"""

import httpx

from services.common.logging import REQUEST_ID_HEADER, get_request_id


class DownstreamError(Exception):
    """A downstream HTTP dependency failed.

    Attributes:
        service: Logical name of the downstream service.
        kind: ``unavailable`` (connection/refused), ``timeout``, or
            ``http_error`` (downstream answered with 4xx/5xx).
        status_code: Downstream HTTP status for ``http_error``, else None.
        detail: Human-readable explanation (logged, never swallowed).
    """

    def __init__(
        self,
        service: str,
        kind: str,
        detail: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(detail)
        self.service = service
        self.kind = kind
        self.detail = detail
        self.status_code = status_code


def post_json(
    service: str,
    url: str,
    payload: dict,
    *,
    timeout_seconds: float,
    request_id: str | None = None,
    client: httpx.Client | None = None,
) -> dict:
    """POST a JSON payload to another service and return its decoded body.

    Args:
        service: Logical downstream name (used in errors/logging).
        url: Absolute downstream URL.
        payload: JSON-serialisable body.
        timeout_seconds: HTTP client timeout.
        request_id: Trace ID to forward; falls back to the in-flight
            request's ID, then to a generated one.
        client: Optional pre-built client (tests inject a mock transport).

    Raises:
        DownstreamError: On connection failure, timeout, non-2xx status,
            or an undecodable response body.
    """
    outgoing_id = request_id or get_request_id()
    headers = {REQUEST_ID_HEADER: outgoing_id} if outgoing_id else {}
    owned = client is None
    client = client or httpx.Client(timeout=timeout_seconds)
    try:
        try:
            response = client.post(url, json=payload, headers=headers)
        except httpx.ConnectError as exc:
            raise DownstreamError(
                service, "unavailable", f"{service} unreachable at {url}: {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise DownstreamError(
                service,
                "timeout",
                f"{service} timed out after {timeout_seconds}s: {exc}",
            ) from exc
        if response.status_code >= 400:
            raise DownstreamError(
                service,
                "http_error",
                f"{service} answered {response.status_code} for {url}",
                status_code=response.status_code,
            )
        try:
            return response.json()
        except ValueError as exc:
            raise DownstreamError(
                service, "http_error", f"{service} returned invalid JSON"
            ) from exc
    finally:
        if owned:
            client.close()