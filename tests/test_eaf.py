from multicastpy.eaf import *


def test_add_orthography(api):
    res = add_orthography(api.data / '2311' / 'mandarin' / 'eaf' / 'mc_mandarin_hml.eaf')
    assert res['0001']
    assert not add_orthography(api.data / '2311' / 'veraa' / 'eaf' / 'mc_veraa_isam.eaf')
