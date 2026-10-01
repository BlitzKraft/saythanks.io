"""Simulation script to demonstrate Issue #106 Facebook callback flow."""
import importlib.util
import os

utils_path = os.path.join(os.path.dirname(__file__), '..', 'saythanks', 'utils.py')
spec = importlib.util.spec_from_file_location("saythanks_utils", utils_path)
saythanks_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(saythanks_utils)
resolve_nickname = saythanks_utils.resolve_nickname

# Sample Facebook user detail without email (e.g. mobile phone account or restricted permissions)
sample_facebook_user = {
    "name": "Sarah Connor",
    "picture": "https://example.com/avatar.jpg"
}
userid = "facebook|9876543210"

# Safe email extraction
raw_email = sample_facebook_user.get('email')
email = raw_email.strip() if isinstance(raw_email, str) and raw_email.strip() else None

# Slug resolution
slug = resolve_nickname(sample_facebook_user, email, userid)

print("--- Simulation Results ---")
print(f"User ID:        {userid}")
print(f"Extracted Email:{email}")
print(f"Generated Slug: {slug}")
print(f"Email Enabled:  {bool(email)}")
print("Status: SUCCESS (Crash-free flow)")
