---
name: Responsive Chromium fixtures
description: Avoid false page-overflow findings from diagnostic output in mobile-emulated browser fixtures.
---

When measuring mobile layouts in a temporary Chromium fixture, hide any inline diagnostic output before interpreting scroll width. Compare the document's client width with its scroll width rather than relying on `window.innerWidth` alone.

**Why:** A long JSON result printed into the fixture widened the mobile layout viewport, falsely suggesting that the site's CSS caused overflow. Once the output was hidden, the width measurements reflected the actual page.

**How to apply:** This matters when constructing small static fixtures or CDP-based responsive checks, not as a reason to ignore overflow observed on the real app.