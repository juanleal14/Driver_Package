from __future__ import annotations

import math

from driver_locator.exceptions import (
    InvalidDriverIdError,
    InvalidLocationError,
    NoDriversAvailableError,
)
from driver_locator.indexes.naive import NaiveDriverIndex
from driver_locator.indexes.protocol import DriverIndex
from driver_locator.models import Driver, DriverId, Location
from driver_locator.repositories.in_memory import InMemoryDriverRepository
from driver_locator.repositories.protocol import DriverRepository


class DriverLocator:
    """Public façade for driver tracking and nearest-driver lookup.

    Depends on ``DriverRepository`` and ``DriverIndex`` protocols, not on
    concrete implementations.  Swap either dependency to change storage or
    search strategy without touching this class.

    >>> locator = DriverLocator()
    >>> locator.upsert_driver("d1", Location(0.0, 0.0))
    >>> locator.find_closest_driver(Location(1.0, 1.0))
    'd1'
    """

    def __init__(
        self,
        repository: DriverRepository | None = None,
        index: DriverIndex | None = None,
    ) -> None:
        self._repository: DriverRepository = repository or InMemoryDriverRepository()
        self._index: DriverIndex = index or NaiveDriverIndex()

    def upsert_driver(self, driver_id: str, location: Location) -> None:
        """Add or update a tracked driver.

        Strips leading/trailing whitespace from ``driver_id`` before storing.
        Raises ``InvalidDriverIdError`` for empty ids.
        Raises ``InvalidLocationError`` for non-finite coordinates.
        """
        validated_id = self._validate_driver_id(driver_id)
        self._validate_location(location)
        driver = Driver(driver_id=validated_id, location=location)
        self._repository.upsert(driver)
        self._index.upsert(driver)

    def stop_tracking(self, driver_id: str) -> None:
        """Stop tracking a driver.  Idempotent — no error for unknown ids."""
        validated_id = self._validate_driver_id(driver_id)
        self._repository.delete(validated_id)
        self._index.remove(validated_id)

    def find_closest_driver(self, location: Location) -> str:
        """Return the id of the closest tracked driver to ``location``.

        Ties are broken by lexicographically smallest driver_id.
        Raises ``NoDriversAvailableError`` when no drivers are tracked.
        Raises ``InvalidLocationError`` for non-finite coordinates.
        """
        self._validate_location(location)
        closest = self._index.find_closest(location)
        if closest is None:
            raise NoDriversAvailableError("No tracked drivers are available.")
        return str(closest)

    # ------------------------------------------------------------------
    # Input validation — kept static so they can be tested independently
    # and reused without constructing a full service instance.
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_driver_id(driver_id: str) -> DriverId:
        if not isinstance(driver_id, str):
            raise InvalidDriverIdError("driver_id must be a string.")
        trimmed = driver_id.strip()
        if not trimmed:
            raise InvalidDriverIdError("driver_id cannot be empty or blank.")
        return DriverId(trimmed)

    @staticmethod
    def _validate_location(location: Location) -> None:
        if not isinstance(location, Location):
            raise InvalidLocationError("location must be a Location instance.")
        if not (math.isfinite(location.x) and math.isfinite(location.y)):
            raise InvalidLocationError("Location coordinates must be finite numbers.")
