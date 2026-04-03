from __future__ import annotations

from math import inf

from driver_locator.indexes._utils import squared_distance
from driver_locator.models import Driver, DriverId, Location


class NaiveDriverIndex:
    """Linear scan index — O(n) find_closest, O(1) upsert/remove.

    Simple and correct. The right default for small fleets or when
    predictable worst-case behaviour matters more than average speed.
    Ties are broken by lexicographically smallest driver_id.
    """

    def __init__(self) -> None:
        self._drivers: dict[DriverId, Driver] = {}

    def upsert(self, driver: Driver) -> None:
        self._drivers[driver.driver_id] = driver

    def remove(self, driver_id: DriverId) -> None:
        self._drivers.pop(driver_id, None)

    def find_closest(self, location: Location) -> DriverId | None:
        best_id: DriverId | None = None
        best_dist = inf

        for driver in self._drivers.values():
            dist = squared_distance(location, driver.location)
            if best_id is None or dist < best_dist:
                best_id = driver.driver_id
                best_dist = dist
            elif dist == best_dist and driver.driver_id < best_id:
                best_id = driver.driver_id

        return best_id
