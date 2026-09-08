import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from saythanks.core import app



def test_compose_offline_route_renders():
    """/compose-offline route must return 200 OK with the submit note form HTML shell."""
    client = app.test_client()
    response = client.get('/compose-offline')

    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert 'id="recipient-user-display"' in html
    assert 'id="thankyou-note-form"' in html
    assert 'id="send-note-btn"' in html
    assert 'handleOfflineSave' in html
    assert 'queueOfflineNote' in html


def test_service_worker_precaches_compose_offline_and_dependencies():
    """sw.js STATIC_ASSETS must precache /compose-offline and local assets, with CDN runtime caching."""
    repo_root = os.path.dirname(os.path.dirname(__file__))
    sw_path = os.path.join(repo_root, 'saythanks', 'static', 'sw.js')

    with open(sw_path, encoding='utf-8') as f:
        sw_content = f.read()

    required_local_assets = [
        '/compose-offline',
        '/static/js/main.js',
        '/static/js/jquery.autogrowtextarea.min.js',
        '/static/js/jquery.simplyCountable.js',
        '/static/js/jquery.modal.min.js',
        '/static/js/offline-outbox.js',
    ]

    for asset in required_local_assets:
        assert asset in sw_content, f"Asset '{asset}' missing from sw.js precache"

    # External CDNs handled in fetch runtime cache instead of install-time addAll
    assert 'uicdn.toast.com' in sw_content
    assert 'ajax.googleapis.com' in sw_content


def test_service_worker_fallback_strategy_handles_to_routes():
    """sw.js must route failed /to/* requests to /compose-offline."""
    repo_root = os.path.dirname(os.path.dirname(__file__))
    sw_path = os.path.join(repo_root, 'saythanks', 'static', 'sw.js')

    with open(sw_path, encoding='utf-8') as f:
        sw_content = f.read()

    assert "url.pathname.startsWith('/to/')" in sw_content
    assert "caches.match('/compose-offline')" in sw_content
