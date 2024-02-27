from clldutils.source import Source

from multicastpy.metadata import *


def test_repl_version():
    assert repl_version('The Version 1234 ', '9999') == 'The Version 9999 '


def test_ReplaceReferences():
    repl = ReplaceReferences()
    res = repl.replace('A [Ref 2023](#ref2023)')
    assert '(Source#cldf:ref2023)' in res
    res = repl.replace('A [Ref 2023](/data/pubs/file.pdf)')
    assert '(MediaTable#cldf:file.pdf)' in res


def test_CorpusMetadata():
    res = CorpusMetadata(
        id='abc',
        lname='Language',
        lgc='abcd1234',
        citation='Cit',
        contributors=['The Author'],
        description='desc',
        image_description='img',
        docs=[],
        texts=[{
            'id': 'textid',
            'type': 'AN',
            'recorded': '1234',
            'speaker': 'SPE1',
            'gender': 'male',
            'age': 'c40',
            'born': 'c1979',
            'local_id': 'lid',
            'title': 'title',
            'description': 'desc'
        }],
        sources=[Source.from_bibtex('@misc{key,\nauthor={A Uther},\ntitle={Title}}')],
    )
    assert res.texts[0].age_estimated and res.texts[0].born_estimated
    assert 'Uther' in res.sources_as_bibtex()
