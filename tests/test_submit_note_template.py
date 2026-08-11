# -*- coding: utf-8 -*-

import os
import re
from io import open


def _read_template():
    """Read the submit-note template as text (Jinja is not rendered)."""
    repository_root = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(
        repository_root, 'saythanks', 'templates', 'submit_note.htm.j2'
    )
    with open(template_path, encoding='utf-8') as template_file:
        return template_file.read()


def _submit_handler():
    """Return the slice of the template starting at the submit listener."""
    template = _read_template()
    marker = "form.addEventListener('submit'"
    assert marker in template, (
        "submit handler not found; did the listener signature change?"
    )
    return template[template.index(marker):]


# Any form control carrying one of these as id/name clobbers the matching
# HTMLFormElement property (form.submit, form.action, form.elements, ...).
CLOBBERING_NAMES = ('submit', 'action', 'method', 'elements', 'reset', 'length')


def test_upload_status_is_set_before_send():
    """Upload status must be initialized before the request is sent."""
    handler = _submit_handler()

    initial_status = u"recordingStatus.innerText = 'Uploading… 0%';"
    send_request = 'request.send(formData);'
    progress_update = (
        u"recordingStatus.innerText = 'Uploading… ' + "
        u"Math.round(e.loaded / e.total * 100) + '%';"
    )

    assert initial_status in handler
    assert progress_update in handler
    assert send_request in handler
    assert handler.index(initial_status) < handler.index(send_request)


def test_submit_button_is_disabled_during_send():
    """The button must be disabled before send to prevent double submission."""
    handler = _submit_handler()

    disable = 'submitBtn.disabled = true;'
    send_request = 'request.send(formData);'

    assert disable in handler
    assert send_request in handler
    assert handler.index(disable) < handler.index(send_request)


def test_submit_button_does_not_shadow_native_form_submit():
    """No form control may be id/name'd such that it clobbers a form property."""
    template = _read_template()

    for attr in ('id', 'name'):
        for value in CLOBBERING_NAMES:
            pattern = re.compile(
                r'''\b%s\s*=\s*['"]%s['"]''' % (attr, value), re.IGNORECASE
            )
            match = pattern.search(template)
            assert match is None, (
                '%s="%s" clobbers HTMLFormElement.prototype.%s; '
                'found at offset %d'
                % (attr, value, value, match.start())
            )

    assert 'id="send-note-btn"' in template
    assert 'document.getElementById("send-note-btn")' in template
