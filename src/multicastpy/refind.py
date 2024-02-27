"""
Handling of refind annotations and referent metadata.
"""
import itertools
import collections

from csvw.dsv import reader, UnicodeWriter

from .xml import updateable_xml

__all__ = ['iter_referents', 'remap_refind', 'refind_map']


def refind_map(tsvdir):
    """
    Map referent indices to dataset-unique integers.
    """
    refinds = collections.OrderedDict()
    for text in sorted(tsvdir.iterdir(), key=lambda p: p.stem):
        refinds['_'.join(text.stem.split('_')[2:])] = {
            r['refind'] for r in reader(text, dicts=True, delimiter='\t') if r['refind']}
    # Compute the number of digits we need for the "old" index.
    refind_length = len(str(max([int(s) for s in itertools.chain(*refinds.values())])))
    res = {}
    for i, (tid, ids) in enumerate(refinds.items(), start=1):
        res[tid] = i
        for refind in ids:
            res[(tid, refind)] = (i * 10 ** refind_length) + int(refind)
    return res


def parse_referent_relations(s):
    """
    The relations of the referent to other referents; including < ‘set member of (partial
    co-reference)’, < ‘includes (split antecedence)’, and M ‘part-whole’; referents with the
    same relation are delimited by commata, and different types of relations by semicola,
    e.g. > 0001, 0002; M 0003.
    """
    rels = collections.defaultdict(set)
    for rel in s.split(';'):
        rel = rel.strip()
        if rel and rel[0] in '<>M':
            rel, refs = rel[0], rel[1:]
        else:
            rel, refs = '', rel
        for ref in refs.split(','):
            ref = ref.strip()
            if ref:
                rels[rel].add(ref)
    return {k: sorted(v) for k, v in rels.items()}


def iter_referents(p, refind_map):
    """
    Read the list-of-referents.tsv file of a corpus.

    :param p:
    :return:
    """
    relid = 0
    for row in reader(p, dicts=True, delimiter='\t'):
        del row['corpus']
        tid = row.pop('text')
        if (tid, row['refind']) in refind_map:
            # Only consider refrents which are actually referenced by REFind indices.
            row['refind'] = refind_map[tid, row['refind']]
            relations = []
            for rel, items in parse_referent_relations(row.pop('relations')).items():
                for item in items:
                    relid += 1
                    relations.append((str(relid), row['refind'], refind_map[tid, item], rel))
            yield row, relations


def remap_refind(p, refind_map):
    """
    Update refind indices in an annotation file according to refind_map.

    :param p:
    :param refind_map:
    :return:
    """
    tid = '_'.join(p.stem.split('_')[2:])
    tid = tid[:-2] if tid.endswith('_a') or tid.endswith('_b') else tid
    if p.suffix == '.eaf':
        with updateable_xml(p, newline='\n') as xml:
            for e in xml.xpath(
                    ".//TIER[@TIER_ID='refind']/ANNOTATION/REF_ANNOTATION/ANNOTATION_VALUE"):
                e.text = str(refind_map[tid, e.text])
    elif p.suffix == '.xml':
        with updateable_xml(p, newline='\r\n') as xml:
            for e in xml.xpath(".//refind"):
                e.text = str(refind_map[tid, e.text])
    elif p.suffix == '.tsv':
        rows = list(reader(p, dicts=True, delimiter='\t'))
        with UnicodeWriter(p, delimiter='\t') as writer:
            for i, row in enumerate(rows):
                if i == 0:
                    writer.writerow(row.keys())
                row['refind'] = str(refind_map[tid, row['refind']] if row['refind'] else '')
                writer.writerow(row.values())
    else:  # pragma: no cover
        raise ValueError(p.suffix)
