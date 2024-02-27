import contextlib
import collections

from lxml.etree import parse, tostring

__all__ = ['UNMARKED', 'updateable_xml', 'get_file', 'text']
UNMARKED = '∅'


@contextlib.contextmanager
def updateable_xml(p, newline='\n'):
    d = parse(p).getroot()
    try:
        yield d
    finally:
        with p.open('w', encoding='utf8', newline=newline) as fp:
            fp.write('<?xml version="1.0" encoding="UTF-8"?>\n{}'.format(
                tostring(d, pretty_print=True, encoding=str)))


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
