import shutil
import pathlib

import multicastpy
from multicastpy.util import *


def test_rmdir(tmp_path):
    assert not rmdir(tmp_path / 'test').exists()
    shutil.copytree(pathlib.Path(multicastpy.__file__).parent / 'data', tmp_path / 'data')
    shutil.copytree(pathlib.Path(multicastpy.__file__).parent / 'data', tmp_path / 'data' / 'data')
    assert tmp_path.joinpath('data').exists()
    assert not rmdir(tmp_path.joinpath('data')).exists()


def test_is_same():
    assert is_same(__file__, __file__)
    assert not is_same(__file__, multicastpy.__file__)
