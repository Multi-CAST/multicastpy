import pathlib

import pytest


@pytest.fixture
def fixtures():
    return pathlib.Path(__file__).parent / 'fixtures'


@pytest.fixture
def api(fixtures):
    from multicastpy.repos import MultiCast
    return MultiCast(fixtures)
