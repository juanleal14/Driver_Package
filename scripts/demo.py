"""End-to-end demo of the driver-locator package.

Run from the repository root:
    python scripts/demo.py
"""
# ruff: noqa: E402  — sys.path must be modified before package imports

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from driver_locator.exceptions import NoDriversAvailableError
from driver_locator.indexes.grid import GridDriverIndex
from driver_locator.models import Location
from driver_locator.service import DriverLocator


def separator(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def main() -> None:
    separator("Basic usage — naive index (default)")

    locator = DriverLocator()
    locator.upsert_driver("driver_1", Location(0.0, 0.0))
    locator.upsert_driver("driver_2", Location(3.0, 4.0))  # distance 5 from origin
    locator.upsert_driver("driver_3", Location(1.0, 1.0))  # distance √2 ≈ 1.41

    query = Location(0.8, 0.9)
    print("\nDrivers: driver_1@(0,0), driver_2@(3,4), driver_3@(1,1)")
    print(f"Query  : {query}")
    print(f"Closest: {locator.find_closest_driver(query)}")  # driver_3

    separator("Updating a driver location")

    locator.upsert_driver("driver_1", Location(0.9, 0.9))  # moves driver_1 very close
    print("\ndriver_1 moved to (0.9, 0.9)")
    print(f"Closest to {query}: {locator.find_closest_driver(query)}")  # driver_1

    separator("Stopping tracking")

    locator.stop_tracking("driver_1")
    print("\ndriver_1 stopped.")
    print(f"Closest to {query}: {locator.find_closest_driver(query)}")  # driver_3

    separator("Tie-breaking by lexicographic driver_id")

    tie_locator = DriverLocator()
    tie_locator.upsert_driver("zebra", Location(1.0, 0.0))
    tie_locator.upsert_driver("alpha", Location(-1.0, 0.0))
    print("\nzebra@(1,0) and alpha@(-1,0) are equidistant from origin.")
    print(f"Winner: {tie_locator.find_closest_driver(Location(0.0, 0.0))}")  # alpha

    separator("NoDriversAvailableError when fleet is empty")

    empty = DriverLocator()
    try:
        empty.find_closest_driver(Location(0.0, 0.0))
    except NoDriversAvailableError as exc:
        print(f"\nCaught expected error: {exc}")

    separator("Idempotent stop_tracking for unknown driver")

    locator.stop_tracking("ghost_driver")  # must not raise
    print("\nstop_tracking('ghost_driver') silently succeeded.")

    separator("Grid index — same API, different strategy")

    grid_locator = DriverLocator(index=GridDriverIndex(cell_size=2.0))
    grid_locator.upsert_driver("g1", Location(0.0, 0.0))
    grid_locator.upsert_driver("g2", Location(10.0, 10.0))
    print(f"\nGrid index, query (1,1): {grid_locator.find_closest_driver(Location(1.0, 1.0))}")

    print("\n✓ All scenarios completed successfully.\n")


if __name__ == "__main__":
    main()
