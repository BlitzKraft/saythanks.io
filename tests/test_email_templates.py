# -*- coding: utf-8 -*-

import importlib.util
import os
import sys
import types

from jinja2 import Environment


ROOT = os.path.dirname(os.path.dirname(__file__))


def _load_myemail():
    """Import myemail.py without booting the Flask app"""
    
    if 'flask' not in sys.modules:
        flask = types.ModuleType('flask')
        flask.url_for = lambda *a, **k: ''
        flask.current_app = None
        sys.modules['flask'] = flask

    if 'mailersend' not in sys.modules:
        mailersend = types.ModuleType('mailersend')
        emails = types.ModuleType('mailersend.emails')
        emails.NewEmail = lambda *a, **k: object()
        mailersend.emails = emails
        sys.modules['mailersend'] = mailersend
        sys.modules['mailersend.emails'] = emails
    
    if 'saythanks' not in sys.modules:
        pkg = types.ModuleType('saythanks')
        pkg.__path__ = [os.path.join(ROOT, 'saythanks')]
        sys.modules['saythanks'] = pkg

    os.environ['MAILERSEND_API_KEY'] = 'test-key'



    def load(name, relpath):
        if name in sys.modules:
            return sys.modules[name]
        spec = importlib.util.spec_from_file_location(
            name, os.path.join(ROOT, relpath)
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    load('saythanks.logging_config', 'saythanks/logging_config.py')
    return load('saythanks.myemail', 'saythanks/myemail.py')

myemail = _load_myemail()

class Note:
    body = '<p>Thanks for the library!</p>'
    byline = 'Ada'


def test_template_objects_select_the_expected_layout():
    url = 'https://saythanks.io/note/abc'
    _, default_html, _ = myemail._build_email_content(
        Note(), url, template=myemail.DEFAULT_TEMPLATE
    )
    _, compressed_html, _ = myemail._build_email_content(
        Note(), url, template=myemail.COMPRESSED_TEMPLATE
    )

    assert Note.body in default_html and Note.body in compressed_html
    assert 'max-width:600px' in compressed_html
    assert '=========' not in compressed_html
    assert '=========' in default_html
    assert 'max-width:600px' not in default_html


def test_notify_uses_template_name_to_select_layout():
    sent = []
    get_url = myemail._get_note_url
    send = myemail._send_email
    myemail._get_note_url = lambda note: 'https://saythanks.io/note/abc'
    myemail._send_email = lambda *args: sent.append(args) or True
    try:
        myemail.notify(Note(), 'owner@example.com', template_name='default')
        myemail.notify(Note(), 'owner@example.com', template_name='compressed')
    finally:
        myemail._get_note_url = get_url
        myemail._send_email = send
    assert sent[0][0] == sent[1][0] == 'owner@example.com'
    assert '=========' in sent[0][2]
    assert 'max-width:600px' in sent[1][2]
    assert '=========' not in sent[1][2]


def test_inbox_toggle_follows_saved_choice():
    path = os.path.join(ROOT, 'saythanks', 'templates', 'inbox.htm.j2')
    with open(path, encoding='utf-8') as handle:
        source = handle.read()
    start = source.index('{% if email_template_name == "default" %}')
    end = source.index('</li>', start) + len('</li>')
    env = Environment()
    env.globals['url_for'] = lambda name, **k: '/' + name.replace('_', '-')
    tpl = env.from_string(source[start:end])
    default_state = tpl.render(email_template_name='default')
    compressed_state = tpl.render(email_template_name='compressed')
    assert '/toggle-template' in default_state and '/toggle-template' in compressed_state
    assert 'compressed email layout' in default_state
    assert 'default email layout' in compressed_state
    assert 'default email layout' not in default_state
    assert 'compressed email layout' not in compressed_state
