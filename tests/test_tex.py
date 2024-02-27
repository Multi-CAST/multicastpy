from multicastpy.tex import *


def test_iter_text_metadata(api):
    gmd = {}
    res = list(iter_text_metadata(
        api.corpora_tex, api.text_metadata('2311'), 'arta', gmd))
    assert res
    assert 'sources' in gmd
    res = list(iter_text_metadata(
        api.corpora_tex, api.text_metadata('2311'), 'tulil', gmd))
    assert res[0]['id'] == 'all1'
    assert res[0]['local_id'] == 'AL_L1'
