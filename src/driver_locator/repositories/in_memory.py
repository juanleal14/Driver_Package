from __future__ import annotations

from driver_locator.models import Driver, DriverId


class InMemoryDriverRepository:
    """Thread-unsafe in-memory store backed by a plain dict.

    Suitable for single-process use.  For concurrent access, wrap with
    a lock or replace with a thread-safe backend via ``DriverRepository``.
    """

    def __init__(self) -> None:
        self._drivers: dict[DriverId, Driver] = {}

    def upsert(self, driver: Driver) -> None:
        self._drivers[driver.driver_id] = driver

    def delete(self, driver_id: DriverId) -> Driver | None:
        return self._drivers.pop(driver_id, None)

    def get(self, driver_id: DriverId) -> Driver | None:
        return self._drivers.get(driver_id)

    def list(self) -> list[Driver]:
        return list(self._drivers.values())

    def __len__(self) -> int:
        return len(self._drivers)
