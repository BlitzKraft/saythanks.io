# -*- coding: utf-8 -*-

import ast
import os
from types import SimpleNamespace


ROOT = os.path.dirname(os.path.dirname(__file__))
CORE_PATH = os.path.join(ROOT, 'saythanks', 'core.py')


def _load_submit_note(namespace):
    with open(CORE_PATH, encoding='utf-8') as core_file:
        tree = ast.parse(core_file.read(), filename=CORE_PATH)

    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == 'submit_note'
    )
    function.decorator_list = []
    module = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, CORE_PATH, 'exec'), namespace)
    return namespace['submit_note']


class _Markup(str):
    def striptags(self):
        return str(self)


def _run_submit_note(email_enabled, content_type='markdown'):
    notifications = []
    captured_url = {}

    class Note:
        def notify(self, *args, **kwargs):
            notifications.append((args, kwargs))

    class Inbox:
        def __init__(self, slug):
            self.slug = slug

        def submit_note(self, **kwargs):
            return Note()

        @staticmethod
        def get_email(slug):
            return 'owner@example.com'

        @staticmethod
        def get_email_template_name(slug):
            return 'default'

        @staticmethod
        def is_email_enabled(slug):
            return email_enabled

    def url_for(endpoint, **kwargs):
        captured_url.update(endpoint=endpoint, **kwargs)
        return '/thanks'

    namespace = {
        'request': SimpleNamespace(
            files={},
            form={
                'body': 'A thank-you note',
                'content-type': content_type,
                'byline': 'Sender',
            },
        ),
        'storage': SimpleNamespace(Inbox=Inbox),
        'Markup': _Markup,
        'Cleaner': lambda **kwargs: SimpleNamespace(
            clean_html=lambda body: body
        ),
        'markdown': lambda body, extensions: body,
        'render_audio_html': lambda audio_filename: '',
        'clean_topic': lambda topic: topic,
        'logger': SimpleNamespace(info=lambda *args: None),
        'redirect': lambda location: location,
        'url_for': url_for,
    }
    submit_note = _load_submit_note(namespace)

    result = submit_note('owner', None)

    return result, captured_url, notifications


def test_submit_note_reports_email_setting_for_both_content_types():
    for content_type in ('markdown', 'html'):
        for email_enabled in (True, False):
            result, redirect_args, notifications = _run_submit_note(
                email_enabled, content_type
            )

            assert result == '/thanks'
            assert redirect_args == {
                'endpoint': 'thanks',
                'status': 'sent',
                'email_forwarded': str(email_enabled).lower(),
            }
            if email_enabled:
                assert len(notifications) == 1
                assert notifications[0][0][0] == 'owner@example.com'
            else:
                assert notifications == []
