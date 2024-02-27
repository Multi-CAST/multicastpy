import re
import pathlib

import attr
from clldutils.markup import MarkdownLink

__all__ = ['CorpusMetadata', 'repl_version', 'ReplaceReferences']


def repl_version(s, version):
    return re.sub('Version [0-9]{4}', 'Version {}'.format(version), s)


class ReplaceReferences:
    def __init__(self):
        self.references = set()
        self.pubs = {}

    def __call__(self, ml):
        if ml.parsed_url.fragment:
            self.references.add(ml.parsed_url.fragment)
            ml.url = 'Source#cldf:{}'.format(ml.parsed_url.fragment)
        elif 'data/pubs' in ml.parsed_url.path:
            path = ml.parsed_url.path
            if path.startswith('/'):
                path = path[1:]
            did = pathlib.Path(ml.url).stem.replace('-', '_')
            self.pubs[pathlib.Path(ml.url).name] = did
            ml.url = 'MediaTable#cldf:{}'.format(did)
        return ml

    def replace(self, text):
        return MarkdownLink.replace(text, self)


@attr.s
class CorpusDoc:
    id = attr.ib(validator=attr.validators.matches_re('^[a-zA-Z0-9_]+$'))
    name = attr.ib()


@attr.s
class CorpusMetadata:
    id = attr.ib(validator=attr.validators.matches_re(r'^[a-z]+$'))
    lname = attr.ib()
    lgc = attr.ib(
        converter=lambda s: 'matu1261' if s is None else s,
        validator=attr.validators.matches_re(r'^[a-z]{4}[0-9]{4}$'))
    citation = attr.ib()
    contributors = attr.ib(
        validator=[attr.validators.min_len(1), attr.validators.instance_of(list)])
    description = attr.ib(validator=attr.validators.min_len(1))
    image_description = attr.ib(validator=attr.validators.min_len(1))
    docs = attr.ib(
        converter=lambda s: [CorpusDoc(id=i, name=n) for n, i in s.items()],
        validator=attr.validators.instance_of(list))
    texts = attr.ib(
        converter=lambda s: [TextMetadata(**ss) for ss in s],
        validator=[attr.validators.min_len(1), attr.validators.instance_of(list)])
    sources = attr.ib(default=attr.Factory(list))
    affiliation = attr.ib(default=None)
    areas = attr.ib(default=None)
    varieties = attr.ib(default=None)

    def __attrs_post_init__(self):
        assert not (self.lgc == 'matu1261' and self.lname != 'Matukar Panau')

    def sources_as_bibtex(self):
        return '\n\n'.join(src.bibtex() for src in self.sources)


@attr.s
class TextMetadata:
    id = attr.ib(validator=attr.validators.matches_re(r'^[a-zA-Z0-9-]+$'))
    type = attr.ib(validator=attr.validators.in_(['TN', 'AN', 'SN']))
    recorded = attr.ib(validator=attr.validators.matches_re('[0-9]{4}'))
    speaker = attr.ib(validator=attr.validators.matches_re('[A-Z0-9]{4}'))
    gender = attr.ib(validator=attr.validators.in_(['male', 'female']))
    age = attr.ib()
    born = attr.ib()
    local_id = attr.ib(converter=lambda s: s.replace(r'\_', '_') if s else s)
    title = attr.ib()
    description = attr.ib()
    born_estimated = attr.ib(default=False)
    age_estimated = attr.ib(default=False)

    def __attrs_post_init__(self):
        for attrib in ['age', 'born']:
            val = getattr(self, attrib)
            setattr(self, attrib + '_estimated', val.startswith('c'))
            setattr(self, attrib, int(val.replace('c', '')))
