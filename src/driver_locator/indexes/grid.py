from __future__ import annotations

import math
from collections import defaultdict

from driver_locator.indexes._utils import squared_distance
from driver_locator.models import Driver, DriverId, Location


class GridDriverIndex:
    """Grid-partitioned index with expanding-ring search and early termination.

    Space is divided into square cells of side ``cell_size``. Lookup starts
    at the query cell (ring 0) and expands outward one ring at a time.

    Early-termination guarantee
    ---------------------------
    After fully scanning ring ``r`` (r ≥ 1), every driver in rings r+1, r+2, …
    is at Euclidean distance ≥ r·cell_size from the query point.  Proof: the
    query point lies inside its cell; the nearest edge of any ring-(r+1) cell
    is at least r cell widths away.  Therefore, if ``(r·cell_size)² > best``
    we can stop — no remaining ring can improve the current candidate.

    Bounding-box max_radius — O(1)
    --------------------------------
    The loop upper bound is computed from a maintained bounding box of occupied
    cell coordinates rather than a full scan of ``self._cells``.  The box is
    expanded eagerly on every upsert (O(1)) and never shrunk on remove —
    giving a slightly conservative upper bound after deletions, but one that is
    always correct.  Early termination handles the actual stopping condition in
    the common case; the bounding box merely prevents an unbounded loop when
    early termination cannot fire (e.g. all drivers equidistant from the query).

    Complexity (uniform random distribution)
    -----------------------------------------
    - upsert / remove : O(1) average
    - find_closest    : sublinear average; O(n) worst case (all drivers
                        equidistant or packed into one cell)

    Choosing cell_size
    ------------------
    Target ~4 drivers per cell on average.  For a fleet spread over an area A:
        cell_size ≈ sqrt(4·A / n_drivers)
    The default of 1.0 suits unit-scale coordinates; the benchmark uses 50.0
    for a ±5 000 coordinate space with tens of thousands of drivers.
    """

    def __init__(self, cell_size: float = 1.0) -> None:
        if cell_size <= 0:
            raise ValueError("cell_size must be positive")
        self._cell_size = cell_size
        self._cells: dict[tuple[int, int], dict[DriverId, Driver]] = defaultdict(dict)
        self._driver_cells: dict[DriverId, tuple[int, int]] = {}
        self._drivers: dict[DriverId, Driver] = {}
        # Bounding box of occupied cell coordinates: (min_cx, max_cx, min_cy, max_cy).
        # Expanded on upsert; never shrunk on remove (conservative upper bound).
        self._bbox: tuple[int, int, int, int] | None = None

    def upsert(self, driver: Driver) -> None:
        prev_cell = self._driver_cells.get(driver.driver_id)
        curr_cell = self._cell_for(driver.location)

        if prev_cell is not None and prev_cell != curr_cell:
            self._cells[prev_cell].pop(driver.driver_id, None)
            if not self._cells[prev_cell]:
                del self._cells[prev_cell]

        self._cells[curr_cell][driver.driver_id] = driver
        self._driver_cells[driver.driver_id] = curr_cell
        self._drivers[driver.driver_id] = driver
        self._expand_bbox(curr_cell)

    def remove(self, driver_id: DriverId) -> None:
        cell = self._driver_cells.pop(driver_id, None)
        self._drivers.pop(driver_id, None)
        if cell is None:
            return
        self._cells[cell].pop(driver_id, None)
        if not self._cells[cell]:
            del self._cells[cell]
        # Bbox is intentionally NOT shrunk here — see class docstring.

    def find_closest(self, location: Location) -> DriverId | None:
        if not self._drivers:
            return None

        query_cell = self._cell_for(location)
        best_id: DriverId | None = None
        best_dist = math.inf

        max_radius = self._max_radius(query_cell)
        for radius in range(max_radius + 1):
            for cell in self._ring_cells(query_cell, radius):
                for driver in self._cells.get(cell, {}).values():
                    dist = squared_distance(location, driver.location)
                    if best_id is None or dist < best_dist:
                        best_id = driver.driver_id
                        best_dist = dist
                    elif dist == best_dist and driver.driver_id < best_id:
                        best_id = driver.driver_id

            # Early termination: drivers in all remaining rings are at
            # Euclidean distance ≥ radius·cell_size from the query point.
            # If that lower bound already exceeds our best squared distance,
            # no future ring can improve the result.
            if radius >= 1 and (radius * self._cell_size) ** 2 > best_dist:
                break

        return best_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cell_for(self, location: Location) -> tuple[int, int]:
        return (
            math.floor(location.x / self._cell_size),
            math.floor(location.y / self._cell_size),
        )

    def _expand_bbox(self, cell: tuple[int, int]) -> None:
        cx, cy = cell
        if self._bbox is None:
            self._bbox = (cx, cx, cy, cy)
        else:
            min_cx, max_cx, min_cy, max_cy = self._bbox
            self._bbox = (
                min(min_cx, cx),
                max(max_cx, cx),
                min(min_cy, cy),
                max(max_cy, cy),
            )

    def _max_radius(self, query_cell: tuple[int, int]) -> int:
        """O(1) upper bound on the Chebyshev distance to any occupied cell.

        Derived from the maintained bounding box — no scan of ``self._cells``
        required.  May be slightly overestimated after removes, which is safe:
        the loop will simply encounter empty cells that cost nothing.
        """
        if self._bbox is None:
            return 0
        qx, qy = query_cell
        min_cx, max_cx, min_cy, max_cy = self._bbox
        return max(abs(qx - min_cx), abs(qx - max_cx), abs(qy - min_cy), abs(qy - max_cy))

    @staticmethod
    def _ring_cells(center: tuple[int, int], radius: int) -> list[tuple[int, int]]:
        """All cells at Chebyshev distance exactly ``radius`` from ``center``."""
        cx, cy = center
        if radius == 0:
            return [(cx, cy)]

        cells: list[tuple[int, int]] = []
        # Top and bottom rows of the ring square
        for x in range(cx - radius, cx + radius + 1):
            cells.append((x, cy - radius))
            cells.append((x, cy + radius))
        # Left and right columns (excluding corners already added)
        for y in range(cy - radius + 1, cy + radius):
            cells.append((cx - radius, y))
            cells.append((cx + radius, y))
        return cells
