import os
from types import SimpleNamespace

from jinja2 import Environment


ROOT = os.path.dirname(os.path.dirname(__file__))
TEMPLATE_PATH = os.path.join(
    ROOT, 'saythanks', 'templates', 'share_note.htm.j2'
)


def _archive_action():
    with open(TEMPLATE_PATH, encoding='utf-8') as template_file:
        template = template_file.read()

    start = "{% if 'profile' in session %}"
    end = '{% endif %}'
    assert start in template
    conditional_start = template.index(start)
    conditional_end = template.index(end, conditional_start) + len(end)
    conditional = template[conditional_start:conditional_end]
    return Environment().from_string(conditional)


def _render_archive_action(profile):
    template = _archive_action()

    def url_for(endpoint, **kwargs):
        assert endpoint == 'archive_note'
        return '/inbox/archive/note/' + kwargs['uuid']

    return template.render(
        session={'profile': profile} if profile is not None else {},
        note=SimpleNamespace(uuid='note-uuid'),
        url_for=url_for,
    )


def test_archive_action_is_only_rendered_for_authenticated_viewers():
    assert _render_archive_action(None).strip() == ''
    assert 'href="/inbox/archive/note/note-uuid"' in _render_archive_action(
        {'nickname': 'owner'}
    )
    assert 'href="/inbox/archive/note/note-uuid"' in _render_archive_action({})


def test_archive_action_has_an_accessible_name():
    archive_action = _render_archive_action({'nickname': 'owner'})

    assert 'aria-label="Archive note"' in archive_action
    assert 'title="Archive note"' in archive_action
