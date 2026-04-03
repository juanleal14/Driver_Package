from __future__ import annotations

from driver_locator.models import Location


def squared_distance(origin: Location, target: Location) -> float:
    """Return squared Euclidean distance between two locations.

    Avoids sqrt for comparison purposes — order is preserved and the
    operation is strictly cheaper.
    """
    dx = origin.x - target.x
    dy = origin.y - target.y
    return dx * dx + dy * dy
