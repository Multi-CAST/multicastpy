import functools
import itertools
import contextlib
import collections

from lxml.etree import parse, tostring
from pyigt import IGT
from pyigt.lgrmorphemes import MORPHEME_SEPARATORS

__all__ = ['UNMARKED', 'updateable_xml', 'get_file', 'text', 'remap_refind']
UNMARKED = '∅'


def iter_words(chunks1, chunks2):
    assert len(chunks1) == len(chunks2)
    word, gloss = '', ''
    for chunk1, chunk2 in zip(chunks1, chunks2):
        if chunk1.endswith('--'):  # We replace double-hyphen with em dash.
            chunk1 = chunk1[:-2] + '—'
        if chunk1.endswith('-') and chunk2 == 'NC':  # Bora specialty?
            chunk1 = chunk1[:-1] + '—'

        if not word:
            word, gloss = chunk1, chunk2
        else:
            if word[-1] in MORPHEME_SEPARATORS or chunk1[0] in MORPHEME_SEPARATORS:
                assert gloss[-1] in MORPHEME_SEPARATORS or chunk2[0] in MORPHEME_SEPARATORS
                if word[-1] == chunk1[0]:  # Separator applied on both sides.
                    chunk1 = chunk1[1:]
                if gloss[-1] == chunk2[0]:  # Separator applied on both sides.
                    chunk2 = chunk2[1:]
                word += chunk1
                gloss += chunk2
            else:
                yield word, gloss
                word, gloss = chunk1, chunk2

    if word:
        yield word, gloss


@contextlib.contextmanager
def updateable_xml(p, newline='\n'):
    d = parse(p).getroot()
    try:
        yield d
    finally:
        with p.open('w', encoding='utf8', newline=newline) as fp:
            fp.write('<?xml version="1.0" encoding="UTF-8"?>\n{}'.format(
                tostring(d, pretty_print=True, encoding=str)))


def remap_refind(doc, refind_map, tid):
    for e in doc.xpath(".//refind"):
        e.text = str(refind_map[tid, e.text])


def iter_text(p, markdown=False):
    for e in p.xpath('child::node()'):
        if getattr(e, 'tag', None):
            if e.tag == 'em':
                yield '*{}*'.format(text(e, markdown=markdown)) if markdown else text(e)
            elif e.tag == 'strong':
                yield '**{}**'.format(text(e)) if markdown else text(e)
            elif e.tag == 'a':
                assert markdown
                yield '[{}]({})'.format(text(e), e.get('href'))
            elif e.tag == 'span':
                yield text(e, markdown=markdown)
            elif e.tag == 'br':
                yield '\n'
        else:
            yield str(e)


def text(e, markdown=False):
    return ''.join(iter_text(e, markdown=markdown)).strip()


def parse_tiers(unit):
    tiers = collections.defaultdict(list)
    tiernames = 'gword gloss graid refind isnref'.split()
    for segment in unit.xpath('annotations/segment'):
        for name in tiernames:
            e = segment.xpath(name)
            if e:
                tiers[name].append(e[0].text or UNMARKED)
            else:
                tiers[name].append(UNMARKED)
    return tiers


class Element:
    def __init__(self, e):
        self.e = e

    def __getattr__(self, item):
        if item in self.e.attrib:
            return self.e.attrib[item]
        raise AttributeError(item)  # pragma: no cover


class Unit(Element):
    def __init__(self, e):
        Element.__init__(self, e)
        for name, tier in parse_tiers(e).items():
            setattr(self, name, tier)
        glossed_words = list(iter_words(self.gword, self.gloss))
        self._gword = [w for w, _ in glossed_words]
        self._gloss = [g for _, g in glossed_words]

    @functools.cached_property
    def igt(self):
        igt = IGT(phrase=self._gword, gloss=self._gloss)
        if igt.conformance.name == 'UNALIGNED':  # pragma: no cover
            print(igt.conformance.name)
            for k, v in itertools.zip_longest(self.gword, self.gloss):
                print(k, v)
            print(self.gword)
            print(self.gloss)
            print('---')
            print(self._gword)
            print(self._gloss)
        return igt

    def __getattr__(self, item):
        if item in [
            'utterance_id',
            'utterance',
            'utterance_translation',
            'add_orthography',
            'add_comments'
        ]:
            for e in self.e.xpath(item):
                return text(e)
            return None
        return Element.__getattr__(self, item)


class File(Element):
    def __iter__(self):
        return (Unit(e) for e in self.e.xpath('unit'))


def get_file(p):
    doc = parse(p).getroot()
    texts = doc.xpath('.//text')
    assert len(texts) == 1
    text = texts[0]
    files = text.xpath('file')
    assert len(files) == 1
    return File(files[0])
