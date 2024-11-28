import json
import wave
import shutil
import pathlib
import functools
import mimetypes
import contextlib

import attr
import ffmpeg
from clldutils.markup import add_markdown_text
from clldutils.path import md5
from cldfbench import Dataset as BaseDataset, CLDFSpec, Metadata
from pycldf import Sources
from csvw.dsv import reader

from .util import rmdir
from .refind import iter_referents, refind_map, remap_refind
from .xml import UNMARKED, get_file
from .eaf import add_orthography


def audio_duration(p):
    if p.suffix == '.wav':
        with contextlib.closing(wave.open(str(p), 'r')) as f:  # pragma: no cover
            return f.getnframes() / float(f.getframerate())
    if p.suffix == '.mp3':
        return float(ffmpeg.probe(str(p))['format']['duration'])
    raise ValueError(f'unknown audio format {p.suffix}')  # pragma: no cover


@attr.s
class MultiCastMetadata(Metadata):
    version = attr.ib(default=None)
    glottocode = attr.ib(default=None)
    affiliation = attr.ib(default=None)
    varieties = attr.ib(default=None)
    areas = attr.ib(default=None)
    language = attr.ib(default=None)
    contributors = attr.ib(default=attr.Factory(list))
    docs = attr.ib(default=attr.Factory(list))
    image_description = attr.ib(default=None)


class Dataset(BaseDataset):
    metadata_cls = MultiCastMetadata

    def cldf_specs(self):  # pragma: no cover
        return CLDFSpec(
            dir=self.cldf_dir,
            module='TextCorpus',
            data_fnames={
                'ContributionTable': 'texts.csv',
                'ExampleTable': 'utterances.csv',
            }
        )

    @functools.cached_property
    def lid(self):
        assert self.id[:2] == 'mc'
        return self.id[2:]

    @functools.cached_property
    def with_refind(self):
        return any(self.refind_map.values())

    @functools.cached_property
    def with_isnref(self):
        for t in self.raw_dir.joinpath('tsv').iterdir():
            for r in reader(t, dicts=True, delimiter='\t'):
                if r.get('isnref'):
                    return True
        return False  # pragma: no cover

    @functools.cached_property
    def refind_map(self):
        return refind_map(self.raw_dir / 'tsv')

    def cmd_readme(self, args):
        res = BaseDataset.cmd_readme(self, args)
        res = add_markdown_text(res, '![](cldf/media/image.jpg)', 'How to cite')
        ds = self.cldf_reader()
        lang = ds.get_object('LanguageTable', self.id)
        lat = float(lang.cldf.latitude)
        lon = float(lang.cldf.longitude)
        res = add_markdown_text(
            res,
            "```geojson\n{}\n```".format(json.dumps({
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        }
                    },
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [lon - 5, lat + 5],
                                    [lon + 5, lat + 5],
                                    [lon + 5, lat - 5],
                                    [lon - 5, lat - 5],
                                    [lon - 5, lat + 5],
                                ]
                            ]
                        }
                    }
                ]
            }, indent=4)),
            'Description')
        cmd = [m for m in ds['MediaTable'] if m['Media_Type'] == 'application/pdf']
        return add_markdown_text(
            res,
            """
## Corpus metadata

{}
""".format('\n'.join(
                '- [{}](cldf/media/{})'.format(
                    r['Name'].replace('.pdf', '').replace('-', ' ').capitalize(), r['Name'])
                for r in cmd)),
            'Description'
        )

    def cmd_makecldf(self, args):

        self.add_schema(args.writer.cldf)

        mdir = rmdir(self.cldf_dir / 'media')
        mdir.mkdir()
        for d in ['eaf', 'tsv', 'xml']:
            for p in self.raw_dir.joinpath(d).glob('*.' + d):
                shutil.copyfile(p, mdir / p.name)
                remap_refind(mdir / p.name, self.refind_map)

        docmap = {}
        for p in ['annotation-notes.pdf',
                  'image.jpg', 'metadata.pdf',
                  'translated-texts.pdf'] + self.metadata.docs:
            p = self.raw_dir / p
            if p.exists():
                docmap[p.name] = md5(p)
                shutil.copyfile(p, mdir / p.name)
                args.writer.objects['MediaTable'].append(dict(
                    ID=docmap[p.name],
                    Name=p.name,
                    Media_Type=mimetypes.guess_type(p.name)[0],
                    Size=p.stat().st_size,
                    Download_URL='{}/{}'.format(mdir.name, p.name),
                ))
        #
        # FIXME: use docmap to fix URLs in description!
        #

        glang = args.glottolog.api.languoid(self.metadata.glottocode)
        args.writer.objects['LanguageTable'].append(dict(
            ID=self.id,
            Name=self.metadata.language,
            Glottocode=glang.id,
            Macroarea=glang.macroareas[0].name,
            Latitude=glang.latitude if glang.latitude else glang.parent.latitude,
            Longitude=glang.longitude if glang.longitude else glang.parent.longitude,
            Affiliation=self.metadata.affiliation,
            Areas=self.metadata.areas,
            Varieties=self.metadata.varieties,
        ))
        args.writer.objects['LanguageTable'].append(dict(
            ID='en',
            Name='English',
            Glottocode='stan1293',
        ))
        args.writer.cldf.sources = Sources.from_file(self.raw_dir / 'sources.bib')

        i = -1
        for i, (row, rels) in enumerate(iter_referents(
            self.raw_dir / 'list-of-referents.tsv',
            self.refind_map,
            log=args.log,
        )):
            if i == 0:
                args.writer.objects['referents.csv'].append(dict(refind=UNMARKED))
            #
            # FIXME: store available refind and only add relations with available id!
            #
            args.writer.objects['referents.csv'].append(row)
            for relid, source, target, rel in rels:
                args.writer.objects['referent_relations.csv'].append(dict(
                    ID=relid, Source_Referent_ID=source, Target_Referent_ID=target, Relation=rel))
        if i < 0:  # pragma: no cover
            assert not self.with_refind
            args.writer.cldf.remove_table('referents.csv')
            args.writer.cldf.remove_table('referent_relations.csv')

        for tid, t in self.raw_dir.read_json('texts.json').items():
            #
            # FIXME: create HTML views of the texts! put in gh-pages?
            #
            cfids, clauses, reclength = [], 0, 0
            for p in mdir.glob('mc_{}_{}*.xml'.format(self.lid, tid)):
                file = get_file(p)
                orthography = add_orthography(mdir / '{}.eaf'.format(p.stem))
                fname = pathlib.Path(file.audio)
                fids = []

                for suffix in ['mp3', 'wav']:
                    path = self.raw_dir / 'audio' / '{}.{}'.format(fname.stem, suffix)
                    if not path.exists():
                        continue
                    fid = path.name.lstrip('mc_{}_'.format(self.lid)).replace('.', '_')
                    fids.append(fid)
                    shutil.copyfile(path, mdir / path.name)
                    args.writer.objects['MediaTable'].append(dict(
                        ID=fid,
                        Name=path.name,
                        Media_Type=mimetypes.guess_type(path.name)[0],
                        Size=path.stat().st_size,
                        Length=audio_duration(path),
                        Contribution_ID=t['id'],
                        Download_URL='{}/{}'.format(mdir.name, path.name),
                    ))

                reclength += args.writer.objects['MediaTable'][-1]['Length']
                for suffix in ['eaf', 'xml', 'tsv']:
                    p = mdir / '{}.{}'.format(fname.stem, suffix)
                    fid = p.name.lstrip('mc_{}_'.format(self.lid)).replace('.', '_')
                    mtype = 'application/eaf+xml' if suffix == 'eaf' \
                        else mimetypes.guess_type(p.name)[0]
                    fids.append(fid)
                    args.writer.objects['MediaTable'].append(dict(
                        ID=fid,
                        Name=p.name,
                        Media_Type=mtype,
                        Size=p.stat().st_size,
                        Contribution_ID=t['id'],
                        Download_URL='{}/{}'.format(mdir.name, p.name),
                    ))

                for unit in file:
                    clauses += 1
                    #
                    # FIXME: Check if unit.refind is available, else warn and replace with None.
                    #
                    args.writer.objects['ExampleTable'].append(dict(
                        ID='{}_{}'.format(tid, unit.uid),
                        Language_ID=self.id,
                        Text_ID=tid,
                        Primary_Text=unit.utterance,
                        Analyzed_Word=unit.gword,
                        Gloss=unit.gloss,
                        Translated_Text=unit.utterance_translation,
                        Comment=unit.add_comments,
                        Audio_Start=int(unit.start_time),
                        Audio_End=int(unit.end_time),  # milliseconds
                        Meta_Language_ID='en',
                        #
                        # FIXME: lgr conformance
                        #
                        graid=unit.graid,
                        refind=unit.refind,
                        refindFK=unit.refind,
                        isnref=unit.isnref,
                        add_orthography=orthography.get(unit.uid),
                        Media_IDs=fids,
                        Contribution_ID=tid,
                    ))
                cfids.extend(fids)
            args.writer.objects['ContributionTable'].append(dict(
                ID=t['id'],
                Name=t['title'] or t['id'],
                Description=t['description'],
                Contributor=self.metadata.contributors,
                Citation=self.metadata.citation,
                Text_Number=self.refind_map[tid],
                Media_IDs=cfids,
                Clause_Count=clauses,
                Speaker=t['speaker'],
                Speaker_Gender=t['gender'],
                Speaker_Age=t['age'],
                Speaker_Age_Approximated=t['age_estimated'],
                Speaker_Year_Born=t['born'],
                Speaker_Year_Born_Approximated=t['born_estimated'],
                Type=t['type'],
                Year_Recorded=int(t['recorded']),
                Recording_Length=reclength,
                Source=sorted(args.writer.cldf.sources.keys()),
            ))

    def add_schema(self, cldf):
        cldf.add_component(
            'LanguageTable',
            {
                "name": "Affiliation",
                "dc:description": "Genealogical affiliation of the language."
            },
            {
                "name": "Areas",
                "dc:description": "Areas where the language is spoken."
            },
            {
                "name": "Varieties",
                "dc:description": "Varieties of the language recorded in this dataset."
            },
        )

        cldf.add_columns(
            'ContributionTable',
            {
                "name": "Text_Number",
                "datatype": "integer",
                "dc:description": "Numeric text identifier, used as prefix of referent indices.",
            },
            {
                "name": "Media_IDs",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#mediaReference",
                "separator": " ",
            },
            {
                "name": "Clause_Count",
                "datatype": "integer",
            },
            'Speaker',
            {
                "name": "Speaker_Gender",
                "datatype": {"base": "string", "format": "male|female"},
            },
            {
                'name': 'Speaker_Age',
                'dc:description': 'The age of the speaker at the time of recording.',
                'datatype': 'integer'
            },
            {
                'name': 'Speaker_Age_Approximated',
                'datatype': {'base': 'boolean', 'format': 'yes|no'},
                'dc:description': 'Whether the age of the speaker was approximated.'
            },
            {
                'name': 'Speaker_Year_Born',
                'dc:description': 'The speaker’s year of birth',
                'datatype': 'integer',
            },
            {
                'name': 'Speaker_Year_Born_Approximated',
                'datatype': {'base': 'boolean', 'format': 'yes|no'},
                'dc:description': 'Whether the year of birth of the speaker was approximated.'
            },
            {
                "name": "Type",
                "dc:description": "TN = traditional narratives, AN = autobiographical narratives, "
                                  "SN = stimulus-based narratives.",
                "datatype": {"base": "string", "format": "TN|SN|AN"},
            },
            {
                "name": "Year_Recorded",
                "datatype": "integer",
            },
            {
                "name": "Recording_Length",
                "datatype": "float",
            },
            {
                "name": "Source",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#source",
                "separator": ";",
            },
        )
        cldf['ContributionTable'].common_props['dc:description'] = \
            "A collection of texts from one language, with shared provenance."
        cldf['ContributionTable', 'Description'].common_props['dc:format'] = 'text/markdown'
        cldf['ContributionTable', 'Contributor'].separator = ' and '

        cldf.add_columns(
            'ExampleTable',
            {
                "name": "Media_IDs",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#mediaReference",
                "separator": " ",
            },
            {
                "name": "Position",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#position",
                "datatype": "integer",
            },
            {
                "name": "Audio_Start",
                "datatype": "integer",
            },
            {
                "name": "Audio_End",
                "datatype": "integer",
            },
            {
                "name": "graid",
                "dc:format": "GRAID 7.0",  # FIXME: there's some GRAID 8.0!
                "dc:description":
                    "A morphosyntactic annotation unit with the GRAID scheme (Grammatical "
                    "relations and animacy in discourse, Haig & Schnell 2014) or ## as clause "
                    "boundary marker.",
                "separator": "\t",
            },
            {
                "name": "add_orthography",
                "dc:description":
                    "The object language text in another orthographical system; in "
                    "Mandarin or Japanese, for instance, this tier contains the text in its "
                    "original orthography (hanzi, or kanji and kana) while the utterance tier "
                    "is a transliteration of the text (pinyin, or romaji)."
            },
            {
                "name": "Text_ID",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#contributionReference",
            },
        )
        if self.with_refind:
            cldf.add_columns(
                'ExampleTable',
                {
                    "name": "refind",
                    "dc:format": "RefIND",
                    "dc:description":
                        "Referent identification with the RefIND scheme (Referent "
                        "indexing in natural-language discourse, Schiborr et al. 2018). {} is used "
                        "to signal no referent information.".format(UNMARKED),
                    "separator": "\t",
                },
                {
                    "name": "refindFK",
                    "dc:description":
                        "A duplicate refind column is provided, to enable checking referential "
                        "integrity (via this list-valued foreign key) while still allowing uniform "
                        "access to the annotation tiers in CLDF SQL. (While the refind column will "
                        "be converted to a TEXT column in CLDF SQL, this column will be replaced "
                        "by an association table.)",
                    "separator": "\t",
                })
        if self.with_isnref:
            cldf.add_columns(
                'ExampleTable',
                {
                    "name": "isnref",
                    "dc:format": "",  # new|bridging|use
                    "dc:description":
                        "The information status of referents with the ISNRef scheme "
                        "(Information status of new referents, Schiborr et al. 2018: "
                        "15), an adaptation of the RefLex scheme (Riester & Baumann 2017). {} is "
                        "used to signal no INNRef annotation.".format(UNMARKED),
                    "separator": "\t",
                })

        cldf['ExampleTable'].common_props['dc:description'] = \
            'Annotated clauses of the texts in the collection.'
        cldf['ExampleTable', 'Analyzed_Word'].separator = '\t'
        cldf['ExampleTable', 'Analyzed_Word'].common_props['dc:description'] = \
            ("A grammatical word in the object language (or #, marking clause boundaries or ZERO "
             "marking zero anaphora). “Word” here should be understood in terms of a GRAID "
             "annotation unit.")
        cldf['ExampleTable', 'Gloss'].separator = '\t'
        cldf['ExampleTable', 'Gloss'].common_props['dc:description'] = \
            ("The morphological glossing for the grammatical word, as per the Leipzig Glossing "
             "Rules. (or #, marking clause boundaries or ZERO marking zero anaphora).")
        cldf.add_component(
            'MediaTable',
            'version',
            {
                "name": "Size",
                "dc:description": "File size in bytes",
                "datatype": "integer",
            },
            {
                "name": "Length",
                "dc:description": "Recording length in seconds for audio files.",
                "datatype": "float",
            },
            {
                "name": "Contribution_ID",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#contributionReference",
            },
            {
                "name": "Date_Updated",
                "datatype": "date",
            },
        )
        cldf.add_table(
            'referents.csv',
            {
                "name": "refind",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#id",
            },
            {
                "name": "label",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#name",
            },
            {
                "name": "description",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#description",
            },
            {
                'name': 'class',
                'datatype': {'base': 'string', 'format': 'hum|anm|inm|bdp|mss|loc|tme|abs'},
                'dc:description':
                    "The semantic class of the referent; one of hum ‘human’, anm ‘non-human "
                    "animate’,inm ‘inanimate’, bdp ‘body part’, mss ‘mass’, loc ‘location’, "
                    "tme ‘time’, or abs ‘abstract’. Only a single label is assigned to a referent, "
                    "even where a group contains entities belonging to multiple classes. In such "
                    "cases humans outweigh other animates, animates outweigh inanimates, and "
                    "inanimates outweigh everything else in no particular order."
            },
            {
                "name": "notes",
                "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#comment",
            },
        )
        if self.with_refind:
            cldf.add_table(
                'referent_relations.csv',
                {
                    "name": "ID",
                    "propertyUrl": "http://cldf.clld.org/v1.0/terms.rdf#id",
                },
                'Source_Referent_ID',
                'Target_Referent_ID',
                {
                    'name': 'Relation',  # M < >
                    'dc:description': """\
The relations of a referent to other referents; including < ‘set member of (partial
co-reference)’, > ‘includes (split antecedence)’, and M ‘part-whole’."""}
            )
            cldf.add_foreign_key(
                'referent_relations.csv', 'Source_Referent_ID', 'referents.csv', 'refind')
            cldf.add_foreign_key(
                'referent_relations.csv', 'Target_Referent_ID', 'referents.csv', 'refind')
            cldf.add_foreign_key('ExampleTable', 'refindFK', 'referents.csv', 'refind')
