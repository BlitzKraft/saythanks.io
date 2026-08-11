# -*- coding: utf-8 -*-

from io import open
import os


def test_upload_status_is_set_before_send():
    """Ensure upload status is initialized before sending."""
    repository_root = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(
        repository_root, 'saythanks', 'templates', 'submit_note.htm.j2'
    )

    with open(template_path, encoding='utf-8') as template_file:
        template = template_file.read()

    submit_start = template.index("form.addEventListener('submit'")
    submit_handler = template[submit_start:]
    initial_status = u"recordingStatus.innerText = 'Uploading… 0%';"
    send_request = 'request.send(formData);'
    progress_update = (
        u"recordingStatus.innerText = 'Uploading… ' + "
        u"Math.round(e.loaded / e.total * 100) + '%';"
    )

    assert initial_status in submit_handler
    assert progress_update in submit_handler
    initial_position = submit_handler.index(initial_status)
    send_position = submit_handler.index(send_request)
    assert initial_position < send_position


def test_submit_button_does_not_shadow_native_form_submit():
    """Ensure the form's submit method is not clobbered by its button."""
    repository_root = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(
        repository_root, 'saythanks', 'templates', 'submit_note.htm.j2'
    )

    with open(template_path, encoding='utf-8') as template_file:
        template = template_file.read()

    assert 'id="submit"' not in template
    assert 'name="submit"' not in template
    assert 'id="submit-note"' in template
    assert 'document.getElementById("submit-note")' in template
