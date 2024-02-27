from multicastpy.html import *


def test_iter_corpus_metadata(api):
    res = list(iter_corpus_metadata(api.repos / 'index.html', ['veraa']))
    assert len(res) == 1
    assert res[0]['id'] == 'veraa'
