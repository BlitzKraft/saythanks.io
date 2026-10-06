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
   When `email` was `None`, the application called `storage.Inbox.disable_email(final_slug)`. When users authenticated with a valid email later, there was no corresponding `else` branch to re-enable their notification preferences in the database.

---

## 2. Technical Solution

The fix is implemented in `saythanks/core.py`:

```python
# 1. Fallback to user_info.get('email') if user_detail_info is empty
userid = user_info['sub']
email = user_detail_info.get('email') or user_info.get('email')
nickname = resolve_nickname(user_detail_info, email, userid)
```

```python
# 2. Re-enable outgoing email notifications when a valid email address is present
final_slug = storage.Inbox.link_or_create(userid, nickname, email)
if not email:
    logger.error('Auth0 userinfo email fetch failed!')
    storage.Inbox.disable_email(final_slug)
    logger.info(
        f"Email notifications disabled for {final_slug} due to missing email."
    )
else:
    storage.Inbox.enable_email(final_slug)
```

### Key Benefits:
- **Provider Agnostic:** Supports Facebook, Google, GitHub, and custom OIDC providers reliably.
- **Surgical & Clean:** Avoids unnecessary complexity, custom parsers, or extra dependencies.
- **Database Consistency:** Ensures `email_enabled` accurately reflects the presence of a verified email address.

---

## 3. Verification
- All 35 pytest unit and integration test suites pass cleanly.
