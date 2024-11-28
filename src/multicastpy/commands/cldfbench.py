"""

"""
import shutil

import attr
from clldutils.markup import Table
from clldutils.jsonlib import dump
from clldutils.clilib import PathType

from multicastpy.repos import MultiCast
from multicastpy.util import is_same


def existing_dir(d):
    if not d.exists():
        d.mkdir()
    return d


def register(parser):
    parser.add_argument('repos', type=PathType(type='dir'))
    parser.add_argument('--corpus', default=None)
    parser.add_argument('--version', default=None)
    parser.add_argument('--target-repos', default=None, type=PathType(type='dir'))


def run(args):
    mc = MultiCast(args.repos)

    if not args.corpus:
        print('Available corpora:')
        for cid in mc.corpora:
            print(cid)
        return

    valid_versions = []

    for version in mc.versions:
        vdir = mc.data / version
        for cdir in vdir.iterdir():
            if cdir.name == args.corpus:
                if valid_versions:
                    last = valid_versions[-1]
                    if is_same(cdir / 'tsv', mc.data / last / cdir.name / 'tsv'):
                        continue
                valid_versions.append(vdir.name)

    if not args.version:
        print('Available versions:')
        for version in valid_versions:
            print(version)
        return

    if args.version not in valid_versions:  # pragma: no cover
        args.log.error('{} is not a valid version for corpus {}. ({})'.format(
            args.version, args.corpus, valid_versions))
        return 256

    if not args.target_repos:  # pragma: no cover
        args.log.error('No --target-repos specified')
        return 256

    datadir = mc.data / args.version / args.corpus
    docsdir = mc.docs
    tdir = args.target_repos
    rdir = existing_dir(tdir / 'raw')

    assert tdir.exists(), str(tdir)

    # seed the raw dir of a cldfbench with files according to the selected corpus and version.
    # copy:
    # - data files (tsv, xml, ...)
    md = mc.metadata(args.version, args.corpus)
    dump({t.id: attr.asdict(t) for t in md.texts}, rdir / 'texts.json', indent=4)
    dump({
        "id": "mc{}".format(args.corpus),
        "title": "Multi-CAST {}".format(md.lname),
        "description": md.description,
        "license": "CC-BY-4.0",
        "url": "https://multicast.aspra.uni-bamberg.de/#{}".format(args.corpus),
        "citation": md.citation,
        "version": args.version,
        "language": md.lname,
        "glottocode": md.lgc,
        "affiliation": md.affiliation,
        "varieties": md.varieties,
        "areas": md.areas,
        "contributors": md.contributors,
        "image_description": md.image_description,
        "docs": md.docs,
    }, rdir.parent / 'metadata.json', indent=4)

    for doc in md.docs:
        fname = doc if isinstance(doc, str) else doc.name
        shutil.copyfile(mc.path('data', 'pubs', fname), rdir / fname)

    #
    # FIXME: write RELEASING.md!
    #

    t = Table('Name', 'Role')
    for name in md.contributors:
        t.append([name, 'Author'])
    t.append(['Geoffrey Haig', 'Editor'])
    t.append(['Stefan Schnell', 'Editor'])
    rdir.parent.joinpath('CONTRIBUTORS.md').write_text(
        '# Contributors\n\n{}'.format(t.render(condensed=False)), encoding='utf8')

    rdir.joinpath('sources.bib').write_text(md.sources_as_bibtex(), encoding='utf8')

    for subdir in datadir.iterdir():
        if subdir.is_dir():
            for p in subdir.iterdir():
                if p.stem == 'mc_{}'.format(args.corpus) or p.suffix == '.zip':  # pragma: no cover
                    continue  # Ignore the aggregated files
                shutil.copyfile(p, existing_dir(rdir / subdir.name) / p.name)

    for suffix in ['mp3', 'wav']:
        if mc.data.joinpath('audio', args.corpus, suffix).exists():
            for p in mc.data.joinpath('audio', args.corpus, suffix).iterdir():
                shutil.copyfile(p, existing_dir(rdir / 'audio') / p.name)

    shutil.copyfile(mc.repos / 'images' / 'mc_{}.jpg'.format(args.corpus), rdir / 'image.jpg')
    for fname, subdir in [
        ('list-of-referents.tsv', 'tsv'),
        ('annotation-notes.pdf', None),
        ('translated-texts.pdf', None),
        ('metadata.pdf', None),
    ]:
        pathcomps = ['corpora', fname.split('.')[0], args.corpus]
        if subdir:
            pathcomps.append(subdir)
        pathcomps.append('mc_{}_{}'.format(args.corpus, fname))
        try:
            shutil.copyfile(docsdir.joinpath(*pathcomps), rdir / fname)
        except FileNotFoundError:  # pragma: no cover
            args.log.warning('No {} available.'.format(fname))

    # non-empty refind / isnref columns in merged tsv determine corresponding feature.
    # empty refind / isnref: 0x2205 - empty set
    # refind -> foreign keys! prefix with integer ID of the text! Must also be done for refinds in
    # "relations"!
    # -> extract referents-list.relations into assoc table referent_relations!

    tdir.joinpath('cldfbench_mc{}.py'.format(args.corpus)).write_text("""\
import pathlib

from multicastpy.dataset import Dataset as BaseDataset


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "mc{}"
""".format(args.corpus), encoding='utf8')

#
# FIXME: some texts are split into several tsv/xml/eaf/audio files! "_a|b" appendix of filename stem
#
