import shutil

import pytest
from lxml.etree import fromstring

from multicastpy.xml import *
from multicastpy.xml import iter_words


@pytest.mark.parametrize(
    'word,gloss,res',
    [
        (['a--', 'b'], ['NC', 'DEM'], [('a—', 'NC'), ('b', 'DEM')]),
        (['a-', 'b'], ['NC', 'DEM'], [('a—', 'NC'), ('b', 'DEM')]),
        (['a=', 'b'], ['NC=', 'DEM'], [('a=b', 'NC=DEM')]),
        (['a=', '=b'], ['NC=', 'DEM'], [('a=b', 'NC=DEM')]),
        (['a-', 'b'], ['NC-', '-DEM'], [('a-b', 'NC-DEM')]),
    ]
)
def test_iter_words(word, gloss, res):
    assert list(iter_words(word, gloss)) == res


@pytest.mark.parametrize(
    'xml,plain,markdown',
    [
        ('the <em>title</em> text', 'the title text', 'the *title* text'),
        ('the <strong>title</strong> text', 'the title text', 'the **title** text'),
        ('the <a href="http://example.com">link</a>', None, 'the [link](http://example.com)'),
        ('two<br/>lines', 'two\nlines', 'two\nlines'),
    ]
)
def test_text(xml, plain, markdown):
    if plain:
        assert text(fromstring('<r>{}</r>'.format(xml))) == plain
    assert text(fromstring('<r>{}</r>'.format(xml)), markdown=True) == markdown


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
