#  utf-8

import os
from io import open


def _layouts():
    """Load render helpers from myemail.py without importing Flask/MailerSend."""
    root = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(root, 'saythanks', 'myemail.py')
    source = open(path, encoding='utf-8').read()
    ns = {}
    exec(
        compile(
            'import html\nfrom string import Template\n'
            + source[
                source.index('DEFAULT_TEMPLATE = '):
                source.index('\ndef _get_note_url(')
            ],
            path,
            'exec',
        ),
        ns,
    )
    return ns


L = _layouts()


def _html(template_id='classic', **kw):
    args = {
        'body': '<p>Thanks.</p>',
        'byline': 'Ada',
        'note_url': 'https://saythanks.io/note/abc',
    }
    args.update(kw)
    return L['render_email_html'](template_id, **args)


def test_unknown_id_falls_back_to_classic():
    assert L['DEFAULT_TEMPLATE'] == 'classic'
    for bad in (None, '', 'nope', '<script>'):
        assert L['resolve_template_id'](bad) == 'classic'
    html = _html('nope')
    assert '=========' in html
    assert 'A note of gratitude' not in html


def test_each_layout_renders():
    markers = {
        'classic': '=========',
        'compact': 'max-width:600px',
        'letter': 'A note of gratitude',
    }
    assert tuple(markers) == L['TEMPLATE_IDS']
    for template_id, marker in markers.items():
        html = _html(template_id)
        assert marker in html
        assert '<p>Thanks.</p>' in html
        assert '--Ada' in html


def test_optional_slots():
    bare = _html()
    assert 'Ref:' not in bare
    assert 'Voice Note' not in bare
    assert 'Ref:' not in _html(topic='   ')
    audio = (
        '<div><strong>Voice Note:</strong> '
        '<a href="https://a.webm">x</a></div>'
    )
    filled = _html(topic='toDo', audio_html=audio)
    assert '<strong>Ref:</strong> about toDo' in filled
    assert 'Voice Note:' in filled


def test_substitution_is_safe():
    html = _html(
        body='Save $5 and {x}',
        byline='A <b>b</b>',
        topic='c <d>',
        note_url='https://x.test/?a=1&b="y"',
    )
    assert 'Save $5 and {x}' in html
    assert '<b>' not in html
    assert '<d>' not in html
    assert '--A &lt;b&gt;b&lt;/b&gt;' in html
    assert 'about c &lt;d&gt;' in html
    assert 'href="https://x.test/?a=1&amp;b=&quot;y&quot;"' in html
