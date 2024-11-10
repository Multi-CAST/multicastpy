import pathlib

import pytest
from cldfbench.datadir import DataDir

from multicastpy.dataset import Dataset


@pytest.fixture
def fixtures():
    return pathlib.Path(__file__).parent / 'fixtures'


@pytest.fixture
def api(fixtures):
    from multicastpy.repos import MultiCast
    return MultiCast(fixtures)


@pytest.fixture
def dataset(tmp_path, fixtures):
    from cldfbench.datadir import DataDir
    from multicastpy.__main__ import main
    target = tmp_path / 'mcveraa'
    target.mkdir()
    main([
        'cldfbench',
        '--corpus', 'veraa',
        '--version', '2311',
        '--target-repos', str(target),
        str(fixtures)])
    ds = Dataset()
    ds.id = 'mcveraa'
    ds.dir = DataDir(target)
    return ds
