from mock import MagicMock, patch, call
import json

from ...helpers import *

from ghtools.exceptions import GithubError
from ghtools.github import Repo


class TestRepo(object):

    def setup(self):
        self.patcher = patch('ghtools.github.repo.make_client')
        self.mock_client_cons = self.patcher.start()
        self.mock_client = self.mock_client_cons.return_value
        self.mock_client.hostname = 'github.test'
        self.r = Repo('test:foo/bar')

    def teardown(self):
        self.patcher.stop()

    def test_raises_if_given_repoless_identifier(self):
        with assert_raises(GithubError):
            Repo('test:foo')

    def test_git_url(self):
        assert_equal(self.r.git_url, 'git@github.test:foo/bar')

    def test_wiki_url(self):
        assert_equal(self.r.wiki_url, 'git@github.test:foo/bar.wiki')

    def test_create_commit_comment(self):
        payload = {'body': 'foobar'}
        self.r.create_commit_comment('deadbeef', payload)
        self.mock_client.post.assert_called_with('/repos/foo/bar/commits/deadbeef/comments',
                                                 data=payload)

    def test_create_hook(self):
        payload = {'foo': 'bar'}
        self.r.create_hook(payload)
        self.mock_client.post.assert_called_with('/repos/foo/bar/hooks',
                                                 data=payload)

    def test_create_issue(self):
        payload = {'foo': 'bar'}
        self.r.create_issue(payload)
        self.mock_client.post.assert_called_with('/repos/foo/bar/issues',
                                                 data=payload)

    def test_create_issue_comment(self):
        issue = {'number': 123}
        payload = {'foo': 'bar'}
        self.r.create_issue_comment(issue, payload)
        self.mock_client.post.assert_called_with('/repos/foo/bar/issues/123/comments',
                                                 data=payload)

    def test_create_pull(self):
        payload = {'foo': 'bar'}
        self.r.create_pull(payload)
        self.mock_client.post.assert_called_with('/repos/foo/bar/pulls',
                                                 data=payload)

    def test_list_commit_comments(self):
        res = self.r.list_commit_comments()
        self.mock_client.paged_get.assert_called_with('/repos/foo/bar/comments')
        assert_equal(res, self.mock_client.paged_get.return_value)

    def test_list_hooks(self):
        res = self.r.list_hooks()
        self.mock_client.paged_get.assert_called_with('/repos/foo/bar/hooks')
        assert_equal(res, self.mock_client.paged_get.return_value)

    def test_list_issues(self):
        res = self.r.list_issues()
        self.mock_client.paged_get.assert_called_with('/repos/foo/bar/issues?direction=asc&state=open')
        assert_equal(res, self.mock_client.paged_get.return_value)

    def test_list_issues_include_closed(self):
        expected_calls = [call('/repos/foo/bar/issues?direction=asc&state=open'),
                          call('/repos/foo/bar/issues?direction=asc&state=closed')]

        self.mock_client.paged_get.side_effect = [[1, 2, 3], [4, 5, 6]]
        res = self.r.list_issues(include_closed=True)
        assert_equal(list(res), [1, 2, 3, 4, 5, 6])
        self.mock_client.paged_get.assert_has_calls(expected_calls)

    def test_list_issue_comments(self):
        issue = {'number': 123}
        res = self.r.list_issue_comments(issue)
        self.mock_client.paged_get.assert_called_with('/repos/foo/bar/issues/123/comments')
        assert_equal(res, self.mock_client.paged_get.return_value)

    def test_list_pulls(self):
        res = self.r.list_pulls()
        self.mock_client.paged_get.assert_called_with('/repos/foo/bar/pulls?direction=asc&state=open')
        assert_equal(res, self.mock_client.paged_get.return_value)

    def test_list_pulls_include_closed(self):
        expected_calls = [call('/repos/foo/bar/pulls?direction=asc&state=open'),
                          call('/repos/foo/bar/pulls?direction=asc&state=closed')]

        self.mock_client.paged_get.side_effect = [[1, 2, 3], [4, 5, 6]]
        res = self.r.list_pulls(include_closed=True)
        assert_equal(list(res), [1, 2, 3, 4, 5, 6])
        self.mock_client.paged_get.assert_has_calls(expected_calls)

    def test_close_issue(self):
        issue = {'number': 123}
        self.r.close_issue(issue)
        self.mock_client.patch.assert_called_with('/repos/foo/bar/issues/123', data={'state': 'closed'})

    def test_open_issue(self):
        issue = {'number': 123}
        self.r.open_issue(issue)
        self.mock_client.patch.assert_called_with('/repos/foo/bar/issues/123', data={'state': 'open'})

    def test_str(self):
        o = Repo('foo/bar')
        assert_equal(str(o), '<Repo foo/bar>')

    def test_str_enterprise(self):
        o = Repo('enterprise:foo/bar')
        assert_equal(str(o), '<Repo enterprise:foo/bar>')
