"""

"""
import urllib.request

from lxml.html import fromstring
from clldutils.clilib import PathType

BASE_URL = "https://multicast.aspra.uni-bamberg.de/"


def dl_dir(url, target):  # pragma: no cover
    if any(d in url for d in ['lilec21', 'sle2020', 'staps17']):
        return
    assert url.startswith(BASE_URL) and url.endswith('/'), 'not a directory entry!'
    dir = target / url.split('/')[-2]
    if not dir.exists():
        dir.mkdir()
    try:
        doc = fromstring(urllib.request.urlopen(url).read())
    except:  # noqa: E722
        return
    for link in doc.xpath('//a'):
        if 'href' not in link.attrib:
            continue
        href = link.attrib['href']
        if href == '../':
            pass
        elif href.endswith('/'):
            dl_dir(url + href, dir)
        else:
            t = dir / href
            if t.suffix == '.zip':
                continue
            if t.exists():
                pass
            else:
                print('{} -> {}'.format(url.replace(BASE_URL, '') + href, dir / href))
                try:
                    urllib.request.urlretrieve(url + href, dir / href)
                except:  # noqa: E722
                    print('failed: {}'.format(url + href))


def register(parser):
    parser.add_argument('repos', type=PathType(type='dir'))


def run(args):  # pragma: no cover
    urllib.request.urlretrieve(BASE_URL, args.repos / 'index.html')
    for d in ['images', 'data']:
        dl_dir(BASE_URL + d + '/', args.repos)
