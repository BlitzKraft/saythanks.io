# Facebook Login troubleshooting

This guide covers two different Facebook authentication problems:

- **“Feature unavailable: Facebook Login is currently unavailable for this app”** is shown by Facebook before it redirects the user to Auth0. The OAuth callback in SayThanks is not reached; check the Facebook app and Auth0 connection configuration first.
- A successful sign-in with no email is a separate issue. Facebook may not return an email address, and SayThanks disables email notifications for an inbox when Auth0 has no email to provide.

## Facebook app setup

In the [Meta for Developers](https://developers.facebook.com/) console, open the Facebook app used by the Auth0 Facebook connection and check:

1. **Facebook Login is configured.** Add the Facebook Login product/use case and configure its web login settings.
2. **The app is available to the intended users.** In Development mode, only app-role users (admins, developers, and testers) can use the app. Switch to Live mode for general users after completing Meta's required app details and review steps. Check the app dashboard for any disabled-app notices or other restrictions.
3. **The redirect URI is Auth0's callback.** Under Facebook Login's OAuth settings, add the exact URI:
   `https://<AUTH0_DOMAIN>/login/callback`
   Replace `<AUTH0_DOMAIN>` with the Auth0 tenant domain, with no extra path or trailing slash.
4. **The app's domains and website details are valid.** Under app settings, set the website's domain and required contact, privacy-policy, and other app details. Use the domain values required by Meta for the app; do not put a redirect URL into the App Domains field.
5. **The email permission is requested if needed.** Facebook users may decline to share an email or have no email address available to the app, so this permission does not guarantee an email will be returned.

If the app is intentionally still in Development mode, add the account used for testing to an appropriate app role rather than expecting sign-in to work for the public.

## Auth0 connection checklist

In the [Auth0 Dashboard](https://manage.auth0.com/), open **Authentication → Social → Facebook** (the exact navigation labels may vary) and verify:

- The Facebook App ID and App Secret match the Facebook app.
- The Facebook connection is enabled for the SayThanks Auth0 application.
- The connection requests the `email` permission if the application needs an email address.
- The Facebook app's **Valid OAuth Redirect URIs** includes Auth0's `https://<AUTH0_DOMAIN>/login/callback`.
- The SayThanks Auth0 application's **Allowed Callback URLs** includes the application's callback URL, `https://<SAYTHANKS_DOMAIN>/callback`.

These are two separate redirects: Facebook returns to Auth0, and Auth0 then returns to SayThanks. Keep each URL on the corresponding allowlist and use the exact deployed domains and paths.

## Diagnose the failure

1. Reproduce the login and note which page displays the error. If Facebook shows “Feature unavailable” before returning to Auth0, check the Facebook app's mode, app roles, Facebook Login settings, app status, and redirect URI. The SayThanks callback has not run in this case.
2. In Auth0, check **Monitoring → Logs** around the attempt. If Auth0 receives the Facebook response, confirm the expected Facebook connection and application were used. If there is no matching Auth0 event, revisit Facebook's app availability and OAuth settings.
3. Once sign-in succeeds, inspect the user's profile in Auth0 and verify whether an `email` value is present. Check the Facebook permission and whether the user granted it, then sign in again after correcting the connection. Do not post access tokens, secrets, or a user's private profile in issue reports.
4. If the user can sign in but has no email in the Auth0 profile, this is not the “Feature unavailable” failure. `saythanks/core.py` looks up the email in the Auth0 user details; when none is returned it logs `Auth0 userinfo email fetch failed!` and disables inbox email notifications. Check the profile/connection response and email permission before investigating application code.

## Official references

- [Meta: Facebook Login for the Web](https://developers.facebook.com/docs/facebook-login/web/)
- [Meta: App Modes](https://developers.facebook.com/docs/development/build-and-test/app-modes/)
- [Meta: Permissions Reference](https://developers.facebook.com/docs/permissions/)
- [Auth0: Facebook social connection](https://auth0.com/docs/authenticate/identity-providers/social-identity-providers/facebook)
- [Auth0: Configure social connections](https://auth0.com/docs/authenticate/identity-providers/social-identity-providers)
