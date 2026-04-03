from __future__ import annotations

import math

import pytest

from driver_locator.exceptions import InvalidDriverIdError, InvalidLocationError
from driver_locator.models import Location
from driver_locator.service import DriverLocator


@pytest.mark.parametrize("bad_id", ["", "   ", "\t", "\n"])
def test_blank_driver_id_rejected(bad_id: str) -> None:
    locator = DriverLocator()
    with pytest.raises(InvalidDriverIdError):
        locator.upsert_driver(bad_id, Location(0.0, 0.0))


def test_non_string_driver_id_rejected() -> None:
    locator = DriverLocator()
    with pytest.raises(InvalidDriverIdError):
        locator.upsert_driver(42, Location(0.0, 0.0))  # type: ignore[arg-type]


def test_non_string_id_rejected_on_stop_tracking() -> None:
    locator = DriverLocator()
    with pytest.raises(InvalidDriverIdError):
        locator.stop_tracking(None)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "x, y",
    [
        (math.nan, 0.0),
        (0.0, math.nan),
        (math.inf, 0.0),
        (-math.inf, 0.0),
        (0.0, math.inf),
        (0.0, -math.inf),
        (math.nan, math.nan),
    ],
)
def test_non_finite_location_rejected_on_upsert(x: float, y: float) -> None:
    locator = DriverLocator()
    with pytest.raises(InvalidLocationError):
        locator.upsert_driver("d1", Location(x, y))


@pytest.mark.parametrize(
    "x, y",
    [(math.nan, 0.0), (0.0, math.inf)],
)
def test_non_finite_location_rejected_on_find_closest(x: float, y: float) -> None:
    locator = DriverLocator()
    locator.upsert_driver("d1", Location(0.0, 0.0))
    with pytest.raises(InvalidLocationError):
        locator.find_closest_driver(Location(x, y))


def test_non_location_instance_rejected() -> None:
    locator = DriverLocator()
    with pytest.raises(InvalidLocationError):
        locator.upsert_driver("d1", (0.0, 0.0))  # type: ignore[arg-type]
