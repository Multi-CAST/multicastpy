

def test_metadata(api):
    res = api.metadata('2311', 'veraa')
    assert res.id == 'veraa'
