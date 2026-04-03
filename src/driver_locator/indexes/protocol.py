from __future__ import annotations

from typing import Protocol, runtime_checkable

from driver_locator.models import Driver, DriverId, Location


@runtime_checkable
class DriverIndex(Protocol):
    """Structural protocol for nearest-driver index implementations.

    Any class that exposes these three methods with compatible signatures
    satisfies the protocol — no inheritance required.

    ``@runtime_checkable`` enables ``isinstance`` checks in tests and
    defensive assertions without imposing a class hierarchy.
    """

    def upsert(self, driver: Driver) -> None:
        """Insert or update a driver in the index."""
        ...

    def remove(self, driver_id: DriverId) -> None:
        """Remove a driver from the index. No-op if not present."""
        ...

    def find_closest(self, location: Location) -> DriverId | None:
        """Return the id of the closest tracked driver, or None if empty."""
        ...
