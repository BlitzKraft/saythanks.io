# -*- coding: utf-8 -*-
"""Tests for issue #288: X (Twitter) and LinkedIn as additional Auth0 logins.

These check the Auth0Lock configuration embedded in the Jinja templates as
text (Jinja is not rendered), the same approach used in
test_submit_note_template.py, since rendering requires a live Flask app
with real Auth0/DB credentials.
"""

import os
import re
from io import open

TEMPLATE_NAMES = ('index.htm.j2', 'thanks.htm.j2')

REQUIRED_CONNECTIONS = ('google-oauth2', 'github', 'facebook', 'twitter', 'linkedin')

ALLOWED_CONNECTIONS_RE = re.compile(
    r'''var\s+allowedConnections\s*=\s*\[([^\]]*)\]'''
)


def _read_template(name):
    repository_root = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(repository_root, 'saythanks', 'templates', name)
    with open(template_path, encoding='utf-8') as template_file:
        return template_file.read()


def _allowed_connections(template):
    """Return the list of connection names in the allowedConnections array."""
    match = ALLOWED_CONNECTIONS_RE.search(template)
    assert match is not None, (
        'allowedConnections array not found; did the Auth0Lock config change?'
    )
    return re.findall(r"'([^']+)'", match.group(1))


def test_allowed_connections_declared_in_every_template():
    for name in TEMPLATE_NAMES:
        template = _read_template(name)
        assert ALLOWED_CONNECTIONS_RE.search(template), (
            '%s has no allowedConnections array' % name
        )


def test_allowed_connections_includes_x_and_linkedin():
    for name in TEMPLATE_NAMES:
        connections = _allowed_connections(_read_template(name))
        assert 'twitter' in connections, (
            "%s: 'twitter' missing from allowedConnections "
            "(Auth0's connection id for X is still 'twitter')" % name
        )
        assert 'linkedin' in connections, (
            "%s: 'linkedin' missing from allowedConnections" % name
        )


def test_allowed_connections_does_not_drop_existing_providers():
    for name in TEMPLATE_NAMES:
        connections = _allowed_connections(_read_template(name))
        for provider in REQUIRED_CONNECTIONS:
            assert provider in connections, (
                '%s: %r missing from allowedConnections' % (name, provider)
            )


def test_both_lock_instances_share_the_same_allowed_connections_variable():
    """options_signup/options_signin must reference the shared variable,
    not a hardcoded/duplicated list, so signup and signin never drift apart.
    """
    for name in TEMPLATE_NAMES:
        template = _read_template(name)
        occurrences = re.findall(
            r'allowedConnections:\s*allowedConnections', template
        )
        assert len(occurrences) == 2, (
            '%s: expected options_signup and options_signin to both use '
            'allowedConnections, found %d reference(s)'
            % (name, len(occurrences))
        )


def test_index_and_thanks_templates_do_not_drift_apart():
    """index.htm.j2 and thanks.htm.j2 duplicate the same Lock config;
    guard against one being updated without the other.
    """
    index_connections = _allowed_connections(_read_template('index.htm.j2'))
    thanks_connections = _allowed_connections(_read_template('thanks.htm.j2'))
    assert index_connections == thanks_connections, (
        'index.htm.j2 and thanks.htm.j2 have different allowedConnections '
        'lists: %r vs %r' % (index_connections, thanks_connections)
    )
