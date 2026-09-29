"""Contracts for the Skeleton base styles and their site-specific overrides."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def rule(css, selector):
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    assert match, selector
    return match.group(1)


def test_grid_templates_use_defined_columns_and_full_width_is_real():
    skeleton = read("saythanks/static/css/skeleton.css")
    assert "width: 100%;" in rule(skeleton, ".u-full-width")
    assert ".twelve.columns {" in skeleton
    for template in ("index", "inbox", "thanks"):
        html = read(f"saythanks/templates/{template}.htm.j2")
        assert 'class="sixteen columns"' not in html
    assert 'class="twelve columns u-textcenter"' in read(
        "saythanks/templates/index.htm.j2"
    )
    assert not re.search(r"@media\s*\([^)]*\)\s*\{\s*\}", skeleton)


def test_responsive_controls_wrap_and_keep_keyboard_focus():
    skeleton = read("saythanks/static/css/skeleton.css")
    site = read("saythanks/static/css/saythanks.css")
    buttons = rule(skeleton, 'input[type="button"]')
    assert "min-height: 44px;" in buttons
    assert "height: auto;" in buttons
    assert "white-space: normal;" in buttons
    fields = rule(skeleton, "select")
    assert "min-height: 44px;" in fields
    assert "height: auto;" in fields
    assert "font-size: 16px;" in rule(site, '.search-form input[type="text"]')
    assert "font-size: 16px;" in rule(site, "#badge-modal textarea")
    assert "font-size: 24px;" in rule(site, "#thankyou-note-form #byline")
    assert 'outline: 3px solid var(--color-focus);' in site
    assert "outline: 0;" not in skeleton


def test_mobile_content_stays_in_local_scrollers():
    skeleton = read("saythanks/static/css/skeleton.css")
    site = read("saythanks/static/css/saythanks.css")
    assert "overflow-wrap: anywhere;" in rule(skeleton, "code")
    assert "overflow-x: auto;" in rule(skeleton, "pre>code")
    assert "overflow-x: auto;" in rule(site, ".content table.u-full-width")
    assert ".notes-grid {" in site
    assert "overflow-x: auto;" in rule(site, ".notes-grid")
    assert "body {\n    overflow-x: hidden;" not in site
    assert "@media (hover: hover) and (pointer: fine)" in skeleton
    assert ".home-inbox-image," in site and "max-height: 25rem;" in site


def test_audio_picker_keyboard_access_and_share_colors_survive():
    site = read("saythanks/static/css/saythanks.css")
    form = read("saythanks/templates/submit_note.htm.j2")
    assert form.index('id="audioFileInput"') < form.index('id="audioFilePickerLabel"')
    picker = rule(site, "#thankyou-note-form #audioFileInput")
    assert "display: none;" not in picker
    assert "clip-path: inset(50%);" in picker
    assert "#audioFileInput:focus-visible + #audioFilePickerLabel" in site
    assert re.search(
        r"\.content a\.x-share,\s*\.content a\.fb-share\s*"
        r"\{[^}]*color: #ffffff;",
        site,
    )