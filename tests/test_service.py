from __future__ import annotations

import pytest

from driver_locator.exceptions import NoDriversAvailableError
from driver_locator.models import Location
from driver_locator.service import DriverLocator


def test_upsert_and_find_closest(locator: DriverLocator) -> None:
    locator.upsert_driver("d1", Location(0.0, 0.0))
    locator.upsert_driver("d2", Location(10.0, 10.0))

    assert locator.find_closest_driver(Location(1.0, 1.0)) == "d1"


def test_upsert_updates_existing_driver_location() -> None:
    locator = DriverLocator()
    locator.upsert_driver("d1", Location(100.0, 100.0))
    locator.upsert_driver("d1", Location(1.0, 1.0))  # moves d1 close to origin

    assert locator.find_closest_driver(Location(0.0, 0.0)) == "d1"


def test_stop_tracking_removes_driver(locator: DriverLocator) -> None:
    locator.upsert_driver("d1", Location(0.0, 0.0))
    locator.upsert_driver("d2", Location(1.0, 1.0))

    locator.stop_tracking("d1")

    assert locator.find_closest_driver(Location(0.0, 0.0)) == "d2"


def test_stop_tracking_is_idempotent_for_unknown_driver(locator: DriverLocator) -> None:
    locator.stop_tracking("ghost")  # must not raise
    locator.upsert_driver("d1", Location(0.0, 0.0))
    locator.stop_tracking("ghost")  # still must not raise

    assert locator.find_closest_driver(Location(0.0, 0.0)) == "d1"


def test_find_closest_raises_when_no_drivers(locator: DriverLocator) -> None:
    with pytest.raises(NoDriversAvailableError):
        locator.find_closest_driver(Location(0.0, 0.0))


def test_find_closest_raises_after_last_driver_removed(locator: DriverLocator) -> None:
    locator.upsert_driver("d1", Location(0.0, 0.0))
    locator.stop_tracking("d1")

    with pytest.raises(NoDriversAvailableError):
        locator.find_closest_driver(Location(0.0, 0.0))


def test_tie_broken_by_lexicographically_smallest_id(locator: DriverLocator) -> None:
    # Both drivers equidistant from origin
    locator.upsert_driver("driver_b", Location(1.0, 0.0))
    locator.upsert_driver("driver_a", Location(-1.0, 0.0))

    assert locator.find_closest_driver(Location(0.0, 0.0)) == "driver_a"


def test_whitespace_trimmed_from_driver_id(locator: DriverLocator) -> None:
    locator.upsert_driver("  d1  ", Location(0.0, 0.0))

    # Trimmed id should be returned
    assert locator.find_closest_driver(Location(0.0, 0.0)) == "d1"
    # stop_tracking with original (untrimmed) id should work
    locator.stop_tracking("  d1  ")
    with pytest.raises(NoDriversAvailableError):
        locator.find_closest_driver(Location(0.0, 0.0))


def test_assessment_example() -> None:
    """Reproduce the exact example from the Cabify assessment spec."""
    locator = DriverLocator()
    locator.upsert_driver("driver0", Location(0, 0))
    locator.upsert_driver("driver1", Location(10, 10))
    locator.upsert_driver("driver2", Location(9, 9))
    locator.upsert_driver("driver0", Location(9, 8))  # update: driver0 moves to 9,8
    locator.stop_tracking("driver2")

    # driver0 @ (9,8): dist² = 0+1 = 1
    # driver1 @ (10,10): dist² = 1+1 = 2
    assert locator.find_closest_driver(Location(9, 9)) == "driver0"


def test_single_driver_always_closest(locator: DriverLocator) -> None:
    locator.upsert_driver("only", Location(999.0, 999.0))

    assert locator.find_closest_driver(Location(0.0, 0.0)) == "only"
    assert locator.find_closest_driver(Location(-500.0, 300.0)) == "only"
