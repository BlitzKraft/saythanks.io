# -*- coding: utf-8 -*-
"""Tests for issue #288: /callback error-handling for non-standard providers.

X and LinkedIn can hand back responses that Google/GitHub/Facebook never
would - an error redirect from the IdP, a failed token exchange, a userinfo
response missing 'sub' - and /callback used to crash outright on these
(a raw KeyError) instead of degrading gracefully. These tests exercise the
three early-return guards added to callback_handling() without touching the
database: the Auth0 HTTP calls are mocked, and storage.Inbox.link_or_create
is patched to fail the test if it's ever reached, since none of these
failure paths should get that far.
"""

from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

from saythanks import core
from saythanks.core import app


def _invoke_callback(query_string):
    """Call callback_handling() directly inside a request context.

    Not app.test_client(): Flask 2.2.5's FlaskClient reads
    werkzeug.__version__, which the installed Werkzeug (3.x) no longer
    exposes - another symptom of this repo's unpinned dependencies (see
    issue #516). test_request_context() doesn't go through that code path.
    """
    with app.test_request_context('/callback' + query_string):
        return core.callback_handling()


def _redirects_to_index(response):
    assert response.status_code == 302
    assert urlparse(response.headers['Location']).path == '/'


@patch('saythanks.core.storage.Inbox.link_or_create')
@patch('saythanks.core.requests.get')
@patch('saythanks.core.requests.post')
def test_idp_error_param_redirects_without_any_requests(mock_post, mock_get, mock_link):
    """Auth0/the IdP redirecting back with ?error= must not attempt a token
    exchange at all - it should redirect straight to the homepage.
    """
    response = _invoke_callback(
        '?error=access_denied&error_description=User+denied+access'
    )

    _redirects_to_index(response)
    mock_post.assert_not_called()
    mock_get.assert_not_called()
    mock_link.assert_not_called()


@patch('saythanks.core.storage.Inbox.link_or_create')
@patch('saythanks.core.requests.get')
@patch('saythanks.core.requests.post')
def test_failed_token_exchange_redirects_without_fetching_userinfo(
    mock_post, mock_get, mock_link
):
    """A token response without 'access_token' (e.g. a rejected client
    authentication) must redirect instead of raising a KeyError, and must
    not go on to call /userinfo.
    """
    mock_post.return_value = MagicMock(json=lambda: {'error': 'access_denied'})

    response = _invoke_callback('?code=some-code')

    _redirects_to_index(response)
    mock_post.assert_called_once()
    mock_get.assert_not_called()
    mock_link.assert_not_called()


@patch('saythanks.core.storage.Inbox.link_or_create')
@patch('saythanks.core.requests.get')
@patch('saythanks.core.requests.post')
def test_missing_sub_in_userinfo_redirects_without_creating_inbox(
    mock_post, mock_get, mock_link
):
    """A /userinfo response without 'sub' must redirect instead of raising,
    and must not reach inbox creation/linking.
    """
    mock_post.return_value = MagicMock(json=lambda: {'access_token': 'fake-token'})
    mock_get.return_value = MagicMock(json=lambda: {})

    response = _invoke_callback('?code=some-code')

    _redirects_to_index(response)
    mock_post.assert_called_once()
    mock_get.assert_called_once()
    mock_link.assert_not_called()
