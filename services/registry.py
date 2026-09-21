"""Microservice base class and registry.

A :class:`Service` describes one deployable unit of the platform. Services
register themselves with a :class:`ServiceRegistry`, which other components
use to discover their peers by name.
"""

from dataclasses import dataclass

SERVICE_STATUSES = ("up", "down", "unknown")


@dataclass(frozen=True)
class ServiceEndpoint:
    """Where and how to reach a single service instance."""

    name: str
    host: str
    port: int
    version: str = "0.1.0"
    status: str = "unknown"

    def address(self) -> str:
        """Return the ``host:port`` address of the service."""
        return f"{self.host}:{self.port}"


class Service:
    """Minimal base class describing a microservice."""

    def __init__(
        self,
        name: str,
        host: str = "127.0.0.1",
        port: int = 8000,
        version: str = "0.1.0",
    ) -> None:
        self.name = name
        self.host = host
        self.port = port
        self.version = version

    def status(self) -> str:
        """Current health status of the service."""
        return "up"

    def endpoint(self) -> ServiceEndpoint:
        """Describe this service as a discoverable endpoint."""
        return ServiceEndpoint(
            name=self.name,
            host=self.host,
            port=self.port,
            version=self.version,
            status=self.status(),
        )

    def register(self, registry: "ServiceRegistry") -> "Service":
        """Register this service with a registry."""
        registry.register(self.endpoint())
        return self


class ServiceRegistry:
    """In-process registry for discovering services by name."""

    def __init__(self) -> None:
        self._endpoints: dict[str, ServiceEndpoint] = {}

    def register(self, endpoint: ServiceEndpoint) -> None:
        """Register (or update) a service endpoint."""
        if endpoint.status not in SERVICE_STATUSES:
            raise ValueError(f"invalid status '{endpoint.status}'")
        self._endpoints[endpoint.name] = endpoint

    def unregister(self, name: str) -> None:
        """Remove a service from the registry."""
        self._endpoints.pop(name, None)

    def get(self, name: str) -> ServiceEndpoint | None:
        """Return the endpoint for a service, or None if unknown."""
        return self._endpoints.get(name)

    def address(self, name: str) -> str | None:
        """Return the ``host:port`` address for a service, or None."""
        endpoint = self.get(name)
        return endpoint.address() if endpoint else None

    def all(self) -> tuple[ServiceEndpoint, ...]:
        """Return a snapshot of every registered endpoint."""
        return tuple(self._endpoints.values())

    def __contains__(self, name: object) -> bool:
        return name in self._endpoints

    def __len__(self) -> int:
        return len(self._endpoints)