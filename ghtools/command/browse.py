from __future__ import print_function

import json

from argh import ArghParser, arg
from ghtools import cli

parser = ArghParser(description="Browse the GitHub API")


@arg('github', nargs='?', help='GitHub instance nickname (e.g "enterprise")')
@arg('url', help='URL to browse')
def browse(args):
    """
    Print the GitHub API response at the given URL
    """
    c = cli.get_client(args.github)
    res = c.get(args.url, _raise=False)

    print('HTTP/1.1 {0} {1}'.format(res.status_code, res.reason))

    for k, v in res.headers.items():
        print("{0}: {1}".format(k, v))

    print()
    if res.json is not None:
        print(json.dumps(res.json, indent=2))
    else:
        print(res.content)
parser.set_default_command(browse)


def main():
    parser.dispatch()

if __name__ == '__main__':
    main()
