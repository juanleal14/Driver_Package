"""Benchmark: NaiveDriverIndex vs GridDriverIndex at increasing fleet sizes.

Run from the repository root:
    python scripts/benchmark.py

The same random driver population (same seed) is used for both strategies
at each N, so the comparison is fair.  Queries are also identical.
"""
# ruff: noqa: E402  — sys.path must be modified before package imports

from __future__ import annotations

import random
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from driver_locator.indexes.grid import GridDriverIndex
from driver_locator.models import Location
from driver_locator.service import DriverLocator

SPACE = 5_000.0  # coordinates drawn from [-SPACE, SPACE]
N_QUERIES = 1_000
N_VALUES = [1_000, 5_000, 10_000, 50_000]
# cell_size tuned so each cell holds ~4 drivers on average:
# area = (2*SPACE)^2, density = N/area → cell = sqrt(4*area/N)
SEED = 42


def _random_location(rng: random.Random) -> Location:
    return Location(rng.uniform(-SPACE, SPACE), rng.uniform(-SPACE, SPACE))


def _build(n: int, cell_size: float, rng: random.Random) -> DriverLocator:
    rng.seed(SEED)  # reset so both strategies see identical populations
    locator = DriverLocator(index=GridDriverIndex(cell_size=cell_size))
    for i in range(n):
        locator.upsert_driver(f"driver_{i}", _random_location(rng))
    return locator


def _build_naive(n: int, rng: random.Random) -> DriverLocator:
    rng.seed(SEED)
    locator = DriverLocator()
    for i in range(n):
        locator.upsert_driver(f"driver_{i}", _random_location(rng))
    return locator


def _run(locator: DriverLocator, queries: list[Location]) -> float:
    start = time.perf_counter()
    for q in queries:
        locator.find_closest_driver(q)
    return time.perf_counter() - start


def _cell_size_for(n: int) -> float:
    area = (2 * SPACE) ** 2
    return (4 * area / n) ** 0.5


def main() -> None:
    rng = random.Random(SEED)

    header = f"{'N':>8}  {'Naive (ms)':>12}  {'Grid (ms)':>11}  {'Speedup':>9}"
    print("\n" + header)
    print("─" * len(header))

    for n in N_VALUES:
        cell_size = _cell_size_for(n)

        # Build both locators with identical populations
        naive = _build_naive(n, rng)
        grid = _build(n, cell_size, rng)

        # Build query set (same for both)
        rng.seed(SEED + 1)
        queries = [_random_location(rng) for _ in range(N_QUERIES)]

        t_naive = _run(naive, queries) * 1000
        t_grid = _run(grid, queries) * 1000
        speedup = t_naive / t_grid if t_grid > 0 else float("inf")

        print(f"{n:>8,}  {t_naive:>12.1f}  {t_grid:>11.1f}  {speedup:>8.1f}x")

    print()


if __name__ == "__main__":
    main()
