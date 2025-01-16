"""
Compute frequency of selected GRAID annotations in the corpus.
"""
import re
import itertools
import collections

from clldutils.clilib import PathType, Table, add_format
from pycldf import Database, Dataset

SQL = """
SELECT graid_symbol(graid.word), count(*)
FROM (
    SELECT row_number() over (order by cid) as rn, word, cid
    FROM (
        WITH split(word, clause, cid) AS (
            SELECT '', f.graid || X'09', f.cldf_id
            FROM ExampleTable AS f
            UNION ALL
            SELECT
                substr(clause, 0, instr(clause, X'09')),
                substr(clause, instr(clause, X'09') + 1),
                cid
            FROM split WHERE clause != ''
        )
        SELECT word, cid FROM split where word != '')
) AS graid
GROUP BY graid_symbol(graid.word)
"""


def graid_symbol(s):
    if s.startswith('##'):
        return '##'
    if s.startswith('#') and s != '#nc':
        return '#'
    m = re.search(r'(?P<x>0|pro|np|other)(?P<y>\.[12hdn])?:(?P<z>[a-z]+)', s)
    if m:
        return '{}{}:{}'.format(
            m.group('x'),
            # We subsume <x>.n:<y> under <x>:<y>.
            m.group('y') if m.group('y') and 'n' not in m.group('y') else '',
            m.group('z'))
    return 'non'


def register(parser):  # pragma: no cover
    parser.add_argument('repos', type=PathType(type='dir'))
    add_format(parser, 'simple')
    parser.add_argument('--clause-boundaries', action='store_true', default=False)


def run(args):  # pragma: no cover
    db = args.repos / 'db.sqlite'
    if db.exists():
        db.unlink()
    db = Database(Dataset.from_metadata(args.repos / 'cldf' / 'TextCorpus-metadata.json'), fname=db)
    db.write_from_tg()

    cols = ['s', 'a', 'ncs', 'p', 'obl', 'g', 'l', 'pred', 'poss', 'other']
    data = collections.OrderedDict(
        (
            '{}{}'.format(f, '.' + p if p else ''),
            collections.OrderedDict((col, 0) for col in cols))
        for f, p in itertools.product(['0', 'pro', 'np', 'other'], ['1', '2', 'h', 'd', None]))

    doublehash, hash = 0, 0

    with db.connection() as conn:
        conn.create_function('graid_symbol', 1, graid_symbol)
        cu = conn.execute(SQL, ())
        for graid, count in cu.fetchall():
            row, _, col = graid.partition(':')
            if row in data and col in data[row]:
                data[row][col] = count
            elif graid == '##':
                doublehash = count
            elif graid == '#':
                hash = count

    if args.clause_boundaries:
        with Table(args, 'GRAID', 'count') as t:
            t.append(['**⟨##⟩**' if args.format == 'pipe' else '⟨##⟩', doublehash])
            t.append(['**⟨#⟩**' if args.format == 'pipe' else '⟨#⟩', hash])
            t.append(['**totals**' if args.format == 'pipe' else 'totals', doublehash + hash])
        return

    with Table(args, *['GRAID'] + ['⟨:{}⟩'.format(c) for c in cols] + ['totals']) as t:
        for graid, row in data.items():
            fmt = '**⟨{}⟩**' if args.format == 'pipe' else '⟨{}⟩'
            t.append([fmt.format(graid)] + [row[c] for c in cols] + [sum(row[c] for c in cols)])
        t.append(
            [''] +  # noqa: W504
            [sum(r[c] for r in data.values()) for c in cols] +  # noqa: W504
            [sum(sum(v.values()) for v in data.values())])
