from __future__ import annotations

from typing import Protocol, runtime_checkable

from driver_locator.models import Driver, DriverId


@runtime_checkable
class DriverRepository(Protocol):
    """Minimal structural protocol for driver storage.

    Declares only the two operations ``DriverLocator`` actually calls.
    Keeping the protocol narrow makes it easy to implement alternative
    backends (Redis, PostgreSQL, …) without carrying unused methods.
    """

    def upsert(self, driver: Driver) -> None:
        """Insert or replace a driver record."""
        ...

    def delete(self, driver_id: DriverId) -> Driver | None:
        """Remove a driver. Returns the removed driver or None if absent."""
        ...
