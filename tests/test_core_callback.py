# -*- coding: utf-8 -*-

"""Regression tests for the Auth callback flow.

This file validates the callback handling path in the app's core logic,
with a focus on rejecting invalid Auth0-derived nicknames before any inbox is
created. It loads the real callback function from source, stubs external
services and session state, and asserts that the user sees the rendered error
page without persisting a profile or creating an inbox.

Tradeoffs: the test is intentionally narrow and highly focused, which keeps it
fast and stable while exercising the real callback logic. The use of AST-based
loading and in-memory stubs is effective for isolating the callback behavior,
but it also makes the test more brittle to internal refactors or changes in
function structure.

Possible enhancements: broaden coverage to the success path for valid
nicknames, add assertions for redirect and session-state behavior on a
successful callback, and include a small matrix of other failure modes such as
Auth0 token exchange errors, missing userinfo, and failed inbox creation.
"""

import ast
import json
import os
from types import SimpleNamespace


ROOT = os.path.dirname(os.path.dirname(__file__))
CORE_PATH = os.path.join(ROOT, 'saythanks', 'core.py')


def _load_callback_handling(namespace):
    """Load the real callback function without importing the Flask app."""
    with open(CORE_PATH, encoding='utf-8') as core_file:
        tree = ast.parse(core_file.read(), filename=CORE_PATH)

    callback = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == 'callback_handling'
    )
    callback.decorator_list = []
    module = ast.Module(body=[callback], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, CORE_PATH, 'exec'), namespace)
    return namespace['callback_handling']


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload


class _Auth0Requests:
    def post(self, url, data=None, headers=None):
        return _Response({'access_token': 'test-access-token'})

    def get(self, url, headers=None):
        if url.endswith('/userinfo?access_token=test-access-token'):
            return _Response({'sub': 'auth0|test-user'})
        return _Response(
            {
                'email': 'person@example.com',
                'nickname': 'ignored-by-test',
            }
        )


def test_callback_rejects_invalid_resolved_nickname_before_creating_inbox():
    """Invalid Auth0 nicknames render an error and never create an inbox."""
    invalid_nicknames = (None, '', '   ', 123)

    for invalid_nickname in invalid_nicknames:
        rendered = []

        def render_template(template_name, **context):
            rendered.append((template_name, context))
            return 'rendered-auth-error'

        class Inbox:
            @staticmethod
            def link_or_create(*args):
                raise AssertionError(
                    'an inbox must not be created for an invalid nickname'
                )

        namespace = {
            'json': json,
            'request': SimpleNamespace(args={'code': 'test-code'}),
            'requests': _Auth0Requests(),
            'session': {},
            'logger': SimpleNamespace(error=lambda *args: None),
            'auth_domain': 'auth.example.com',
            'auth_jwt_v2': 'test-management-token',
            'auth_id': 'test-client-id',
            'auth_secret': 'test-client-secret',
            'get_callback_url': lambda: 'https://example.com/callback',
            'resolve_nickname': lambda *args: invalid_nickname,
            'render_template': render_template,
            'storage': SimpleNamespace(Inbox=Inbox),
            'redirect': lambda location: location,
            'url_for': lambda endpoint: '/' + endpoint,
        }
        callback_handling = _load_callback_handling(namespace)

        result = callback_handling()

        assert result == 'rendered-auth-error'
        assert len(rendered) == 1
        template_name, context = rendered[0]
        assert template_name == 'index.htm.j2'
        assert context['callback_url'] == 'https://example.com/callback'
        assert context['auth_id'] == 'test-client-id'
        assert context['auth_domain'] == 'auth.example.com'
        assert 'AUTH0_JWT_V2_TOKEN' in context['auth_error']
        assert 'nickname' not in namespace['session']['profile']