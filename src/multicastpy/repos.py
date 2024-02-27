import re
import pathlib
import functools

from clldutils.apilib import API
from csvw.dsv import reader
from pycldf.sources import Sources

from .html import iter_corpus_metadata
from .tex import iter_text_metadata
from .metadata import CorpusMetadata, repl_version, ReplaceReferences

__all__ = ['MultiCast']
PKG_DIR = pathlib.Path(__file__).parent


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
        return bibtex.strip()  # pragma: no cover

    def metadata(self, version, corpus=None):
        if version not in self.versions:
            raise ValueError('{} is not a valid version'.format(version))  # pragma: no cover

        tmd = self.text_metadata(version)
        corpora_in_version = {r['corpus'] for r in tmd}

        res = {d['id']: d for d in iter_corpus_metadata(self.repos / 'index.html', self.corpora)}
        for cid in corpora_in_version:
            if not corpus or (corpus == cid):
                cmd = res[cid]
                cmd['texts'] = list(
                    iter_text_metadata(self.corpora_tex, self.text_metadata(version), cid, cmd))
                cmd['citation'] = self.citation(cid, version=version)

                desc_repl = ReplaceReferences()
                cmd['description'] = desc_repl.replace(cmd['description'])
                cmd['sources'] = [
                    self.sources[sid] for sid in
                    sorted(desc_repl.references.union(cmd['sources']))]
                cmd['docs'] = desc_repl.pubs

        res = {cid: CorpusMetadata(**d) for cid, d in res.items() if cid in corpora_in_version}
        return res if not corpus else res[corpus]
