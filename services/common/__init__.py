"""Shared, dependency-free utilities for the distributed microservices.

Each business service (order, payment, notification, ...) imports from this
package only. Services never import each other directly; all runtime
communication happens over HTTP.
"""