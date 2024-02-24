import re
import pathlib
import functools
import mimetypes
import urllib.parse

import attr
from clldutils.apilib import API
from clldutils.markup import MarkdownLink
from csvw.dsv import reader
from pycldf.sources import Sources

from .html import iter_corpus_metadata
from .tex import iter_text_metadata

PKG_DIR = pathlib.Path(__file__).parent
URL = "https://multicast.aspra.uni-bamberg.de/"
PARSED_URL = urllib.parse.urlparse(URL)


def repl_version(s, version):
    return re.sub('Version [0-9]{4}', 'Version {}'.format(version), s)


def make_url(path):
    url = urllib.parse.urlparse(path)
    if url.scheme:
        return path
    url = urllib.parse.urlparse(URL)
    return urllib.parse.urlunparse((url.scheme, url.netloc, path, '', '', ''))


class ReplaceReferences:
    def __init__(self, mc):
        self.references = set()
        self.pubs = {}
        self.mc = mc

    def __call__(self, ml):
        if ml.parsed_url.fragment:
            self.references.add(ml.parsed_url.fragment)
            ml.url = 'Source#cldf:{}'.format(ml.parsed_url.fragment)
        elif 'data/pubs' in ml.parsed_url.path:
            path = ml.parsed_url.path
            if path.startswith('/'):
                path = path[1:]
            assert self.mc.path(path).exists(), ml.url
            did = pathlib.Path(ml.url).stem.replace('-', '_')
            self.pubs[pathlib.Path(ml.url).name] = did
            ml.url = 'MediaTable#cldf:{}'.format(did)
        return ml


@attr.s
class CorpusDoc:
    id = attr.ib(validator=attr.validators.matches_re('^[a-zA-Z0-9_]+$'))
    name = attr.ib()

    @property
    def mimetype(self):
        return mimetypes.guess_type(self.name)[0]


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
    age = attr.ib()#>----  c[integer] -> split in age and age_estimated True/False
    born = attr.ib()    # c[year]  -> split in born and born_estimated True/False
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


class MultiCast(API):
    @functools.cached_property
    def data(self):
        return self.path('data')

    @functools.cached_property
    def docs(self):
        return self.data / 'docs'

    @functools.cached_property
    def versions(self):
        return sorted(
            d.name for d in self.data.iterdir() if re.fullmatch('[0-9]{4}', d.name))

    @functools.cached_property
    def corpora(self):
        pattern = re.compile('mc_(?P<cid>[a-z]+)_citation')
        return sorted(
            pattern.match(d.stem).group('cid')
            for d in self.docs.joinpath('citations').glob('*.txt') if pattern.match(d.stem))

    @property
    def corpora_tex(self):
        return self.docs / 'tex' / 'docs' / 'collection-overview' / 'sections' / 'corpora.tex'

    def text_metadata(self, version):
        return reader(
            self.docs / 'general' / 'metadata' / '{}__mc_metadata.tsv'.format(version),
            delimiter='\t',
            dicts=True)

    @functools.cached_property
    def sources(self):
        return Sources.from_file(PKG_DIR / 'data' / 'sources.bib')

    def citation(self, corpus, format='txt', version=None):
        _, citation, bibtex = self.docs.joinpath(
            'citations',
            'mc_{}_citation.txt'.format(corpus)).read_text(encoding='utf8').split('\n\n')
        if version:
            citation = repl_version(citation, version)
        if format == 'txt':
            return citation.strip()
        return bibtex.strip()

    def metadata(self, version, corpus=None):
        if version not in self.versions:
            raise ValueError('{} is not a valid version'.format(version))

        tmd = self.text_metadata(version)
        corpora_in_version = {r['corpus'] for r in tmd}

        res = {d['id']: d for d in iter_corpus_metadata(self.repos / 'index.html', self.corpora)}
        for cid in corpora_in_version:
            cmd = res[cid]
            cmd['texts'] = list(
                iter_text_metadata(self.corpora_tex, self.text_metadata(version), cid, cmd))
            cmd['citation'] = self.citation(cid, version=version)

            desc_repl = ReplaceReferences(self)
            cmd['description'] = MarkdownLink.replace(cmd['description'], desc_repl)
            cmd['sources'] = [
                self.sources[sid] for sid in
                sorted(desc_repl.references.union(cmd['sources']))]
            cmd['docs'] = desc_repl.pubs

        res = {cid: CorpusMetadata(**d) for cid, d in res.items() if cid in corpora_in_version}
        return res if not corpus else res[corpus]
