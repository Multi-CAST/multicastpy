"""
  - `cldf splitmedia cldf`
  - `git commit -a -m"..." .`
  - `git tag -a vXXXX -m"..."`
  - `git push origin`
  - `git push origin --tags`
"""
from clldutils.clilib import PathType

from .makecldf import Repos


def register(parser):  # pragma: no cover
    parser.add_argument('repos', type=PathType(type='dir'))


def run(args):  # pragma: no cover
    repos = Repos(args.repos)
    print(repos.git('commit -a -m "{}"'.format(repos.version)))
    print(repos.git('tag -a v{0} -m "{0}"'.format(repos.version)))
    print(repos.git('push origin'))
    print(repos.git('push origin --tags'))
