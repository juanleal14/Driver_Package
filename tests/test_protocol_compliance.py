"""Verify that concrete implementations satisfy their declared protocols.

Tests are dual-purpose:
  1. Runtime structural check via isinstance (requires @runtime_checkable).
  2. Static type check via mypy — the ``impl: DriverIndex`` annotation forces
     mypy to verify that each parametrised value is a valid protocol instance.
"""

from __future__ import annotations

import pytest

from driver_locator.indexes.grid import GridDriverIndex
from driver_locator.indexes.naive import NaiveDriverIndex
from driver_locator.indexes.protocol import DriverIndex
from driver_locator.models import Driver, DriverId, Location
from driver_locator.repositories.in_memory import InMemoryDriverRepository
from driver_locator.repositories.protocol import DriverRepository

# ---------------------------------------------------------------------------
# DriverIndex protocol
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "impl",
    [NaiveDriverIndex(), GridDriverIndex(cell_size=1.0)],
    ids=["naive", "grid"],
)
def test_driver_index_isinstance(impl: DriverIndex) -> None:
    assert isinstance(impl, DriverIndex)


@pytest.mark.parametrize(
    "impl",
    [NaiveDriverIndex(), GridDriverIndex(cell_size=1.0)],
    ids=["naive", "grid"],
)
def test_driver_index_full_lifecycle(impl: DriverIndex) -> None:
    d1 = Driver(driver_id=DriverId("d1"), location=Location(1.0, 0.0))
    d2 = Driver(driver_id=DriverId("d2"), location=Location(5.0, 0.0))

    # Empty index returns None
    assert impl.find_closest(Location(0.0, 0.0)) is None

    # After one upsert, that driver is closest
    impl.upsert(d1)
    assert impl.find_closest(Location(0.0, 0.0)) == DriverId("d1")

    # After a second upsert, nearest is returned
    impl.upsert(d2)
    assert impl.find_closest(Location(0.0, 0.0)) == DriverId("d1")
    assert impl.find_closest(Location(6.0, 0.0)) == DriverId("d2")

    # Remove closest — second driver takes over
    impl.remove(DriverId("d1"))
    assert impl.find_closest(Location(0.0, 0.0)) == DriverId("d2")

    # Remove last — back to None
    impl.remove(DriverId("d2"))
    assert impl.find_closest(Location(0.0, 0.0)) is None

    # Removing unknown id is a no-op
    impl.remove(DriverId("ghost"))


# ---------------------------------------------------------------------------
# DriverRepository protocol
# ---------------------------------------------------------------------------


def test_driver_repository_isinstance() -> None:
    repo: DriverRepository = InMemoryDriverRepository()
    assert isinstance(repo, DriverRepository)


def test_driver_repository_full_lifecycle() -> None:
    repo: DriverRepository = InMemoryDriverRepository()
    driver = Driver(driver_id=DriverId("d1"), location=Location(1.0, 2.0))

    repo.upsert(driver)
    removed = repo.delete(DriverId("d1"))
    assert removed == driver

    # Second delete returns None
    assert repo.delete(DriverId("d1")) is None
