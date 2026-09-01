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


def test_original_flag_selects_the_layout():
    url = 'https://saythanks.io/note/abc'
    _, current, _ = myemail._build_email_content(Note(), url)
    _, original, _ = myemail._build_email_content(
        Note(), url, original=True
    )

    assert Note.body in current and Note.body in original
    assert 'max-width:600px' in current
    assert '=========' not in current
    assert '=========' in original
    assert 'max-width:600px' not in original


def test_notify_sends_html_for_the_original_flag():
    sent = []
    get_url = myemail._get_note_url
    send = myemail._send_email
    myemail._get_note_url = lambda note: 'https://saythanks.io/note/abc'
    myemail._send_email = lambda *args: sent.append(args) or True
    try:
        myemail.notify(Note(), 'owner@example.com')
        myemail.notify(Note(), 'owner@example.com', original=True)
    finally:
        myemail._get_note_url = get_url
        myemail._send_email = send
    assert sent[0][0] == sent[1][0] == 'owner@example.com'
    assert 'max-width:600px' in sent[0][2]
    assert '=========' in sent[1][2]


def test_inbox_toggle_follows_saved_choice():
    path = os.path.join(ROOT, 'saythanks', 'templates', 'inbox.htm.j2')
    with open(path, encoding='utf-8') as handle:
        source = handle.read()
    start = source.index("{% if is_original_template")
    end = source.index('</li>', start) + len('</li>')
    env = Environment()
    env.globals['url_for'] = lambda name, **k: '/' + name.replace('_', '-')
    tpl = env.from_string(source[start:end])
    on = tpl.render(is_original_template=True)
    off = tpl.render(is_original_template=False)
    assert '/toggle-template' in on and '/toggle-template' in off
    assert 'current e-mail layout' in on
    assert 'original layout' in off
    assert 'original layout' not in on
    assert 'current e-mail layout' not in off
