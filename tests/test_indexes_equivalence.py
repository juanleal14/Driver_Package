"""Property-based tests comparing GridDriverIndex against NaiveDriverIndex.

Hypothesis generates hundreds of random upsert/delete/query sequences.
Any discrepancy between the two implementations surfaces as a falsifying
example with a minimal repro.
"""

from __future__ import annotations

from collections.abc import Sequence

import hypothesis.strategies as st
import pytest
from hypothesis import given, settings

from driver_locator.exceptions import NoDriversAvailableError
from driver_locator.indexes.grid import GridDriverIndex
from driver_locator.models import Location
from driver_locator.service import DriverLocator

# ---------------------------------------------------------------------------
# Shared strategies
# ---------------------------------------------------------------------------

finite_coord = st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False)
location_st = st.builds(Location, x=finite_coord, y=finite_coord)
driver_id_st = st.text(
    alphabet=st.characters(min_codepoint=97, max_codepoint=122),
    min_size=1,
    max_size=6,
)
entry_st = st.tuples(driver_id_st, location_st)
operation_st = st.tuples(st.sampled_from(["upsert", "delete"]), driver_id_st, location_st)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_pair(
    entries: Sequence[tuple[str, Location]], cell_size: float = 20.0
) -> tuple[DriverLocator, DriverLocator]:
    naive = DriverLocator()
    grid = DriverLocator(index=GridDriverIndex(cell_size=cell_size))
    for driver_id, location in entries:
        naive.upsert_driver(driver_id, location)
        grid.upsert_driver(driver_id, location)
    return naive, grid


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@settings(max_examples=200)
@given(entries=st.lists(entry_st, min_size=1, max_size=80), query=location_st)
def test_grid_matches_naive_after_bulk_upsert(
    entries: Sequence[tuple[str, Location]], query: Location
) -> None:
    naive, grid = _build_pair(entries)
    assert grid.find_closest_driver(query) == naive.find_closest_driver(query)


@settings(max_examples=150)
@given(ops=st.lists(operation_st, min_size=1, max_size=120), query=location_st)
def test_grid_matches_naive_after_mixed_ops(
    ops: Sequence[tuple[str, str, Location]], query: Location
) -> None:
    naive = DriverLocator()
    grid = DriverLocator(index=GridDriverIndex(cell_size=10.0))

    for action, driver_id, location in ops:
        if action == "upsert":
            naive.upsert_driver(driver_id, location)
            grid.upsert_driver(driver_id, location)
        else:
            naive.stop_tracking(driver_id)
            grid.stop_tracking(driver_id)

    try:
        expected = naive.find_closest_driver(query)
    except NoDriversAvailableError:
        with pytest.raises(NoDriversAvailableError):
            grid.find_closest_driver(query)
        return

    assert grid.find_closest_driver(query) == expected


@settings(max_examples=100)
@given(
    entries=st.lists(
        st.tuples(
            driver_id_st,
            st.builds(
                Location,
                x=st.floats(-10, 10, allow_nan=False, allow_infinity=False),
                y=st.floats(-10, 10, allow_nan=False, allow_infinity=False),
            ),
        ),
        min_size=1,
        max_size=30,
    ),
    query=st.builds(
        Location,
        x=st.floats(-10, 10, allow_nan=False, allow_infinity=False),
        y=st.floats(-10, 10, allow_nan=False, allow_infinity=False),
    ),
)
def test_grid_early_termination_does_not_affect_correctness(
    entries: Sequence[tuple[str, Location]], query: Location
) -> None:
    """Stress early-exit with many rings: cell_size=0.1 over a ±10 space (200×200 grid)."""
    naive, grid = _build_pair(entries, cell_size=0.1)
    assert grid.find_closest_driver(query) == naive.find_closest_driver(query)


@settings(max_examples=100)
@given(
    entries=st.lists(entry_st, min_size=2, max_size=40),
    to_remove=driver_id_st,
    query=location_st,
)
def test_stopped_driver_never_returned(
    entries: Sequence[tuple[str, Location]], to_remove: str, query: Location
) -> None:
    """A removed driver must never appear as the closest, for both index types."""
    naive = DriverLocator()
    grid = DriverLocator(index=GridDriverIndex(cell_size=10.0))

    for driver_id, location in entries:
        naive.upsert_driver(driver_id, location)
        grid.upsert_driver(driver_id, location)

    naive.stop_tracking(to_remove)
    grid.stop_tracking(to_remove)

    for locator in (naive, grid):
        try:
            result = locator.find_closest_driver(query)
        except NoDriversAvailableError:
            continue
        assert result != to_remove.strip(), (
            f"Removed driver '{to_remove.strip()}' was returned as closest"
        )
