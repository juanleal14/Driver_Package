from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

DriverId = NewType("DriverId", str)


@dataclass(frozen=True, slots=True)
class Location:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Driver:
    driver_id: DriverId
    location: Location
