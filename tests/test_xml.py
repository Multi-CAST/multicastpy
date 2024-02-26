import shutil

from multicastpy.xml import *


def test_get_file(fixtures):
    file = get_file(fixtures / 'data' / '2311' / 'veraa' / 'xml' / 'mc_veraa_isam.xml')
    assert file.audio == 'mc_veraa_isam.wav'
    for unit in file:
        assert unit.uid
        assert unit.graid
        assert unit.utterance
        assert unit.add_orthography is None
        break


def test_updateable_xml(fixtures, tmp_path):
    tp = tmp_path / 'test.xml'
    shutil.copyfile(fixtures / 'data' / '2311' / 'veraa' / 'xml' / 'mc_veraa_isam.xml', tp)
    with updateable_xml(tp) as xml:
        for e in xml.xpath('.//utterance'):
            e.text = 'teststuff'
            break
    assert 'teststuff' in tp.read_text(encoding='utf8')
