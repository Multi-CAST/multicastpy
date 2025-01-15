"""
  - `cldfbench makecldf --with-zenodo --with-cldfreadme --glottolog-version v cldfbench_<dsid>.py`
  - `cldfbench readme cldfbench_<dsid>.py`
  - `cldf validate cldf`


  - `cldf splitmedia cldf`
  - `git commit -a -m"..." .`
  - `git tag -a vXXXX -m"..."`
  - `git push origin`
  - `git push origin --tags`
"""
import shlex
import subprocess

from clldutils.jsonlib import load
from clldutils.clilib import PathType


def cmd(line):  # pragma: no cover
    return subprocess.check_output(shlex.split(line), stderr=subprocess.STDOUT).decode('utf8')


class Repos:  # pragma: no cover
    def __init__(self, p):
        self.dir = p
        md = load(self.dir / 'metadata.json')
        assert md['id'].startswith('mc')
        self.id = md['id']
        self.version = md['version']
        self.mod = self.dir / 'cldfbench_{}.py'.format(self.id)
        assert self.mod.exists()

    def git(self, line):
        return cmd('git -C {} {}'.format(self.dir, line))


def register(parser):  # pragma: no cover
    parser.add_argument('repos', type=PathType(type='dir'))
    parser.add_argument('--glottolog-version', default='v5.1')


def run(args):  # pragma: no cover
    repos = Repos(args.repos)
    print(cmd(
        'cldfbench makecldf --with-zenodo --with-cldfreadme --glottolog-version {} {}'.format(
            args.glottolog_version, repos.mod,
        )))
    print(cmd('cldfbench readme {}'.format(repos.mod)))
    print(cmd('cldf validate {}'.format(args.repos / 'cldf')))
    print(cmd('cldf splitmedia {}'.format(args.repos / 'cldf')))
    print(repos.git('status'))
