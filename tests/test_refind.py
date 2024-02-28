import shutil
import logging

import pytest

from multicastpy.refind import *


@pytest.fixture
def rmap(api):
    return refind_map(api.path('data', '2311', 'veraa', 'tsv'))


def test_iter_referents(api, rmap, caplog):
    assert len(rmap) == 59
    assert max(list(rmap.values())) == 158
    with caplog.at_level(logging.WARNING):
        res = list(iter_referents(
            api.path(
                'data',
                'docs',
                'corpora', 'list-of-referents', 'veraa', 'tsv', 'mc_veraa_list-of-referents.tsv'),
            rmap,
            log=logging.getLogger(__name__)))
    assert len(caplog.records) == 2


def test_remap_refind(api, rmap, tmp_path):
    d = api.path('data', '2311', 'veraa')
    for dd in d.iterdir():
        for p in dd.iterdir():
            shutil.copyfile(p, tmp_path / p.name)
            remap_refind(tmp_path / p.name, rmap)
