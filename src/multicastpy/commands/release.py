"""

"""
from clldutils.clilib import PathType

from .makecldf import Repos, cmd


def register(parser):  # pragma: no cover
    parser.add_argument('repos', type=PathType(type='dir'))
    parser.add_argument('version')


def run(args):  # pragma: no cover
    version = args.version
    if not version.startswith('v'):
        version = 'v' + version
    print(cmd('git -C {} checkout {}'.format(args.repos, version)))

    repos = Repos(args.repos)
    assert repos.version == version[1:]
    repos.dir.joinpath('relnotes.txt').write_text(
        """\
Cite the original dataset as

> {}

and the CLDF dataset as

DOI""".format(repos.md['citation']),
        encoding='utf8')
    print('gh release create v{} --verify-tag --title "{}" --notes-file relnotes.txt'.format(
        repos.version, repos.md['title']))
    print('')
    print("Now you should grab the Zenodo version DOI from\n"
          "https://zenodo.org/account/settings/github/repository/Multi-CAST/{0}\n"
          "and add it to\n"
          "https://github.com/Mulit-CAST/{0}/releases/edit/v{1}\n and the concept DOI to "
          "metdata.json".format(repos.md['id'], repos.version))
