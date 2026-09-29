# -*- coding: utf-8 -*-

"""Tests for the placeholder name style option in display_submit_note().

Confirms that:
- With no 'name_style' option given, the existing American-name behaviour
  is unchanged (backwards compatible).
- With '?name_style=indian', the Indian name generator is used instead.
"""

import ast
import os
from types import SimpleNamespace


ROOT = os.path.dirname(os.path.dirname(__file__))
CORE_PATH = os.path.join(ROOT, 'saythanks', 'core.py')


def _load_display_submit_note(namespace):
    """Load the real display_submit_note without importing the Flask app."""
    with open(CORE_PATH, encoding='utf-8') as core_file:
        tree = ast.parse(core_file.read(), filename=CORE_PATH)

    func = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == 'display_submit_note'
    )
    func.decorator_list = []
    module = ast.Module(body=[func], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, CORE_PATH, 'exec'), namespace)
    return namespace['display_submit_note']


def _abort(code):
    """Stand-in for Flask's abort(): fail the test if it is ever called."""
    raise AssertionError(f'unexpected abort({code})')


def _build_namespace(name_style_value):
    """Build a fake environment so the function can run outside the real app."""
    captured = {}

    def render_template(template_name, **context):
        captured['template'] = template_name
        captured['context'] = context
        return 'rendered'

    class Inbox:
        @staticmethod
        def does_exist(inbox_id):
            return True

        @staticmethod
        def is_enabled(inbox_id):
            return True

    args = {'name_style': name_style_value} if name_style_value else {}
    config = SimpleNamespace(get=lambda key, default=None: default)

    namespace = {
        'storage': SimpleNamespace(Inbox=Inbox),
        'abort': _abort,
        'request': SimpleNamespace(args=args),
        'get_full_name': lambda: 'John Smith',
        'indian_names': SimpleNamespace(get_full_name=lambda: 'Nisha Asthana'),
        'unquote': lambda s: s,
        'render_template': render_template,
        'app': SimpleNamespace(config=config),
    }
    return namespace, captured


def test_default_name_style_is_unchanged_american_behaviour():
    """No 'name_style' option given -> existing American-name behaviour."""
    namespace, captured = _build_namespace(name_style_value=None)
    display_submit_note = _load_display_submit_note(namespace)

    display_submit_note('someuser', '')

    assert captured['context']['fake_name'] == 'John Smith'


def test_indian_name_style_uses_indian_names_package():
    """'?name_style=indian' -> Indian name generator is used instead."""
    namespace, captured = _build_namespace(name_style_value='indian')
    display_submit_note = _load_display_submit_note(namespace)

    display_submit_note('someuser', '')

    assert captured['context']['fake_name'] == 'Nisha Asthana'
