from __future__ import annotations

import pytest

from driver_locator.indexes.grid import GridDriverIndex
from driver_locator.indexes.naive import NaiveDriverIndex
from driver_locator.service import DriverLocator


@pytest.fixture
def locator() -> DriverLocator:
    """Fresh DriverLocator backed by the default naive index."""
    return DriverLocator()


@pytest.fixture
def naive_index() -> NaiveDriverIndex:
    return NaiveDriverIndex()


@pytest.fixture
def grid_index() -> GridDriverIndex:
    """Grid index with cell_size=1.0 for fine-grained fixture use in tests."""
    return GridDriverIndex(cell_size=1.0)
