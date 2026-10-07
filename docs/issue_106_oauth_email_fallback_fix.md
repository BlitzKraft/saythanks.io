# Issue #106: OAuth Email Fallback & Notification Sync Resolution

## Overview
This document provides a technical overview of the root cause and resolution for **Issue #106** regarding OAuth authentication and email notification syncing in `saythanks.io`.

---

## 1. Problem Statement & Root Cause

During social authentication (e.g., Facebook or Google OAuth) mediated by Auth0:

1. **Email Extraction Gap:**
   In `saythanks/core.py` (Line 647), the `/callback` handler extracted user email addresses exclusively from the Auth0 Management API endpoint (`user_detail_info`):
   ```python
   email = user_detail_info.get('email')
   ```
   For social identity providers, `user_detail_info` may omit the email or fail to populate if Management API tokens expire or have restricted scopes. However, the standard OAuth user profile (`user_info`) retrieved directly from `/userinfo` contains the verified email. Without checking `user_info`, `email` evaluated to `None`.

2. **One-Way Notification Disabling:**
   When `email` was `None`, the application called `storage.Inbox.disable_email(final_slug)`. This was intentional for phone-only Facebook signups with no email. However, an earlier version of this fix incorrectly added `else: storage.Inbox.enable_email()` which would silently re-enable notifications for users who had explicitly opted out via `/disable-email`. This has been corrected.

   **Note:** As confirmed in `saythanks/sqls/schema.sql` (line 71), a brand-new inbox is already `email_enabled = DEFAULT true` upon creation. No explicit re-enabling is needed at login.

---

## 2. Technical Solution

The fix is implemented in `saythanks/core.py` — **1 file, 1 line change**:

```python
# Fallback to user_info.get('email') if user_detail_info is empty/restricted
userid = user_info['sub']
email = user_detail_info.get('email') or user_info.get('email')
nickname = resolve_nickname(user_detail_info, email, userid)
```

```python
# Only disable notifications when no email is available (e.g. phone-only Facebook)
# User's explicit opt-out via /disable-email is preserved — no enable_email() on login
final_slug = storage.Inbox.link_or_create(userid, nickname, email)
if not email:
    logger.error('Auth0 userinfo email fetch failed!')
    storage.Inbox.disable_email(final_slug)
    logger.info(
        f"Email notifications disabled for {final_slug} due to missing email."
    )
```

### Key Benefits:
- **Provider Agnostic:** Supports Facebook, Google, GitHub, and custom OIDC providers reliably.
- **Preserves User Preferences:** Explicit `/disable-email` opt-outs are never overwritten on re-login.
- **Schema Aligned:** Relies on `email_enabled DEFAULT true` in schema for new inboxes — no redundant DB writes.
- **Surgical & Clean:** 1 file, 1 line change — no extra dependencies or complexity.

---

## 3. Verification
- All 35 pytest unit and integration test suites pass cleanly.
