# -*- coding: utf-8 -*-

import os
import re
import json


ROOT = os.path.dirname(os.path.dirname(__file__))
STATIC_ROOT = os.path.join(ROOT, 'saythanks', 'static')


def _read(relative_path):
    path = os.path.join(ROOT, relative_path)
    with open(path, encoding='utf-8') as source_file:
        return source_file.read()


def test_service_worker_is_root_registered_and_has_offline_fallback():
    """"""
    base_template = _read('saythanks/templates/base.htm.j2')
    service_worker = _read('saythanks/static/service-worker.js')

    assert "navigator.serviceWorker.register('/service-worker.js')" in base_template
    assert "const OFFLINE_URL = '/static/offline.html';" in service_worker
    assert "caches.match(OFFLINE_URL)" in service_worker
    assert "function matchCachedNavigation(request)" in service_worker
    assert "url.pathname !== '/thanks'" in service_worker


def test_service_worker_precaches_public_note_assets():
    service_worker = _read('saythanks/static/service-worker.js')
    expected_assets = (
        '/static/offline.html',
        '/thanks',
        '/static/manifest.json',
        '/static/css/saythanks.css',
        '/static/js/main.js',
        '/static/images/owly.svg',
    )

    for asset in expected_assets:
        assert asset in service_worker

    assert "cache.addAll(PRECACHE_URLS)" in service_worker
    assert os.path.isfile(os.path.join(STATIC_ROOT, 'offline.html'))


def test_service_worker_does_not_cache_private_routes_or_non_get_requests():
    service_worker = _read('saythanks/static/service-worker.js')

    for private_route in (
        "'/inbox'",
        "'/inbox/search'",
        "'/inbox/archived'",
        "'/logout'",
        "'/callback'",
    ):
        assert private_route in service_worker

    assert "request.method !== 'GET'" in service_worker
    assert "url.origin !== self.location.origin" in service_worker


def test_service_worker_versioned_cache_removes_old_caches():
    service_worker = _read('saythanks/static/service-worker.js')
    compact_worker = re.sub(r'\s+', '', service_worker)

    assert re.search(
        r"const CACHE_NAME = 'saythanks-public-v\d+';", service_worker)
    assert "cacheNames.filter(cacheName=>cacheName!==CACHE_NAME)" in compact_worker
    assert "caches.delete(cacheName)" in service_worker


def test_service_worker_cache_version_changes_for_new_offline_code():
    service_worker = _read('saythanks/static/service-worker.js')

    assert "const CACHE_NAME = 'saythanks-public-v4';" in service_worker


def test_android_manifest_has_install_and_display_metadata():
    manifest = json.loads(_read('saythanks/static/manifest.json'))

    assert manifest['scope'] == '/'
    assert manifest['start_url'] == '/'
    assert manifest['display'] == 'standalone'
    assert manifest['orientation'] == 'portrait-primary'
    assert manifest['theme_color'] == '#3ac025'
    assert all(icon['purpose'] == 'any maskable' for icon in manifest['icons'])


def test_network_status_is_exposed_as_an_accessible_live_region():
    base_template = _read('saythanks/templates/base.htm.j2')

    assert '<span id="network-status" role="status" aria-live="polite"></span>' in base_template
    assert "window.addEventListener('online', updateNetworkStatus)" in base_template
    assert "window.addEventListener('offline', updateNetworkStatus)" in base_template


def test_note_form_has_mobile_responsive_and_touch_friendly_controls():
    """"""
    base_template = _read('saythanks/templates/base.htm.j2')
    css = _read('saythanks/static/css/saythanks.css')
    submit_template = _read('saythanks/templates/submit_note.htm.j2')

    assert '<meta name="theme-color" content="#3ac025">' in base_template
    assert '@media (max-width: 775px)' in css
    assert 'min-height: 44px;' in css
    assert '#thankyou-note-form .form-row {' in css
    assert 'flex-direction: column;' in css
    assert 'font-size: 16px;' in css
    assert '<div class="form-row">' in submit_template
    assert 'autocomplete="name"' in submit_template


def test_note_form_uses_indexeddb_and_keys_drafts_by_form_action():
    """"""
    submit_template = _read('saythanks/templates/submit_note.htm.j2')

    assert "const draftDatabaseName = 'saythanks-pwa';" in submit_template
    assert "const draftStoreName = 'drafts';" in submit_template
    assert "const draftKey = form.getAttribute('action');" in submit_template
    assert "indexedDB.open(draftDatabaseName, 2)" in submit_template
    assert "createObjectStore(draftStoreName, { keyPath: 'key' })" in submit_template
    assert "objectStore(draftStoreName).put({" in submit_template
    assert "key: draftKey," in submit_template
    assert "const outboxStoreName = 'outbox';" in submit_template
    assert "createObjectStore(outboxStoreName, { keyPath: 'id' })" in submit_template
    assert "status: 'queued'," in submit_template
    assert "createOutboxId()" in submit_template
    assert "new URL(form.getAttribute('action'), window.location.href).href" in submit_template


def test_note_form_restores_and_saves_body_and_byline():
    """Test that the note form restores and saves the body and byline fields."""
    submit_template = _read('saythanks/templates/submit_note.htm.j2')

    assert "editor.setMarkdown(draft.body)" in submit_template
    assert "document.getElementById('byline').value = draft.byline" in submit_template
    assert "body: editor.getMarkdown()," in submit_template
    assert "byline: document.getElementById('byline').value," in submit_template
    assert "editor.addHook('change', () => {" in submit_template
    assert (
        "document.getElementById('byline').addEventListener("
        "'input', scheduleDraftSave)"
    ) in submit_template


def test_offline_outbox_retries_on_startup_and_reconnection():
    """"""
    submit_template = _read('saythanks/templates/submit_note.htm.j2')

    assert "window.addEventListener('online', () => syncOutbox()" in submit_template
    assert "syncOutbox().catch(() => {});" in submit_template
    assert "updateOutboxStatus(record.id, 'sending')" in submit_template
    assert "updateOutboxStatus(record.id, 'failed', error.message)" in submit_template
    assert "await deleteOutbox(record.id);" in submit_template


def test_audio_is_stored_in_offline_outbox():
    """Test that audio is stored in the offline outbox and sent with the note."""
    submit_template = _read('saythanks/templates/submit_note.htm.j2')

    assert "const offlineAudio = audioBlob || audioFileInput.files[0] || null;" in submit_template
    assert "audioBlob: offlineAudio," in submit_template
    assert "audioFileName: audioFileName," in submit_template
    assert "formData.append('audio', record.audioBlob, record.audioFileName);" in submit_template


def test_submission_redirects_to_shared_thanks_statuses():
    """Test that submissions redirect to the appropriate thanks statuses."""
    submit_template = _read('saythanks/templates/submit_note.htm.j2')

    assert "window.location.href = '/thanks?status=queued';" in submit_template
    assert "window.location.href = '/thanks?status=sent';" in submit_template


def test_thanks_page_reports_delivery_status_and_waiting_count():
    """"""
    thanks_template = _read('saythanks/templates/thanks.htm.j2')

    assert '<div id="delivery-status" role="status" aria-live="polite">' in thanks_template
    assert "new URLSearchParams(window.location.search).get('status')" in thanks_template
    assert "Note saved to offline outbox." in thanks_template
    assert "Your note was sent successfully." in thanks_template
    assert "const outboxStoreName = 'outbox';" in thanks_template
    assert "getAll();" in thanks_template
    assert "Sending saved notes..." in thanks_template
    assert "await sendRecord(record);" in thanks_template
    assert "await deleteRecord(record.id);" in thanks_template
    assert "formData.append('audio', record.audioBlob, record.audioFileName);" in thanks_template
    assert "window.addEventListener('online', updateStatus);" in thanks_template


def test_offline_fallback_does_not_claim_to_send_notes():
    """"""
    offline_page = _read('saythanks/static/offline.html')

    assert 'Your note drafts remain on this device' in offline_page
    assert 'are not sent until you submit them while connected' in offline_page
