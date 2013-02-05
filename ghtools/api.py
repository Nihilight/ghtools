from datetime import datetime
from os import environ as env
import json
import logging
import urlparse
import requests

from ghtools import __version__
from ghtools.exceptions import GithubError, GithubAPIError

log = logging.getLogger(__name__)

DEFAULT_GITHUB = 'public'

KNOWN_GITHUBS = {
    'public': 'https://api.github.com'
}


class GithubAPIClient(object):
    def __init__(self, root=None, nickname=None):
        self._session = requests.Session()
        self._session.headers['content-type'] = 'application/json'

        if nickname is not None:
            self.nickname = nickname
        else:
            self.nickname = DEFAULT_GITHUB
        self.token = self._env('oauth_token')

        # Try to ascertain GitHub API root
        if root is not None:
            self.root = root
        elif self._env('api_root') is not None:
            self.root = self._env('api_root')
        else:
            try:
                self.root = KNOWN_GITHUBS[self.nickname]
            except KeyError:
                msg = "No known API root for nickname '{0}'. Perhaps you need to set ${1}?".format(
                    self.nickname,
                    envkey(self.nickname, 'api_root')
                )
                raise GithubError(msg)

        # Use specified SSL CA Bundle if provided
        ca_bundle = self._env('ca_bundle')
        if ca_bundle is not None:
            self._session.verify = ca_bundle

        log.debug("Created %s", self)

    def _env(self, key, default=None):
        return env.get(
            envkey(self.nickname, key),
            default
        )

    def _req(self, method, url, _raise=True, *args, **kwargs):
        if "data" in kwargs and (isinstance(kwargs['data'], int) or isinstance(kwargs['data'], dict)):
            kwargs['data'] = json.dumps(kwargs['data'])

        if env.get("GHTOOLS_DEBUG", False):
            print(method, url, args, kwargs)
        res = self._session.request(method, url, *args, **kwargs)
        if env.get("GHTOOLS_DEBUG", False):
            print(res, res.text, res.headers)
        if _raise:
            custom_raise_for_status(res)
        return res

    def _url(self, path):
        return self.root + path

    def login(self, username, password, scopes=None):
        if scopes is None:
            scopes = []

        ver = __version__
        now = datetime.utcnow().replace(microsecond=0)

        note = 'ghtools {0} (created {1})'.format(ver, now.isoformat())

        data = {
            'note': note,
            'scopes': scopes,
        }

        res = self.post(
            '/authorizations',
            auth=(username, password),
            data=json.dumps(data)
        )

        self.token = res.json['token']

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, tok):
        self._token = tok
        if tok is not None:
            self._session.headers['Authorization'] = 'token {0}'.format(self._token)

    @property
    def logged_in(self):
        return self.token is not None

    @property
    def hostname(self):
        return urlparse.urlparse(self.root).netloc.split(':')[0]

    def request(self, method, url, *args, **kwargs):
        return self._req(method, self._url(url), *args, **kwargs)

    def delete(self, url, *args, **kwargs):
        return self._req('delete', self._url(url), *args, **kwargs)

    def get(self, url, *args, **kwargs):
        return self._req('get', self._url(url), *args, **kwargs)

    def patch(self, url, *args, **kwargs):
        return self._req('patch', self._url(url), *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self._req('post', self._url(url), *args, **kwargs)

    def put(self, url, *args, **kwargs):
        return self._req('put', self._url(url), *args, **kwargs)

    def paged_get(self, url, *args, **kwargs):
        for res in paged(self._session, 'get', self._url(url)):
            for repo in res.json:
                yield repo

    def __str__(self):
        return '<GithubAPIClient {0}={1}>'.format(self.nickname, self.root)


def envkey(nickname, key):
    return 'GITHUB_{0}_{1}'.format(nickname.upper(), key.upper())


def paged(session, method, url, **kwargs):
    res = session.request(method, url, **kwargs)

    custom_raise_for_status(res)

    while True:
        yield res
        try:
            next_page = res.links['next']
        except KeyError:
            break
        else:
            res = session.request(method, next_page['url'], **kwargs)
            custom_raise_for_status(res)


def custom_raise_for_status(res):
    try:
        res.raise_for_status()
    except requests.RequestException as err:
        newerr = GithubAPIError(err)
        for k, v in err.__dict__.items():
            setattr(newerr, k, v)
        raise newerr
