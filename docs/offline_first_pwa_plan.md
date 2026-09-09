## Status Review and Next Incremental Improvement

## Recommended Next Incremental Step
_Updated: 2026-09-09T00:00:00Z_

The recent pull already adds a substantial PWA foundation: install metadata and mobile configuration, service-worker registration and versioned cache management, an offline fallback page, a public-network-status live region, IndexedDB draft persistence, an offline outbox queue, queued-note retry handling, and thank-you status pages for delivery states. In practical terms, the app is no longer at the “bare shell” stage; it is now in the validation-and-hardening phase.

The most useful next incremental improvement is to focus on end-to-end offline reliability and correctness of the queued submission flow, especially the parts that are most likely to cause real user-facing failure:

1. Validate the browser flow for offline draft recovery, queue creation, retry-on-reconnect, and queue cleanup.
2. Verify that queued submissions do not silently duplicate delivery when the connection returns, and ensure retries are tied to a stable idempotency key.
3. Check the status UX for failed, queued, sending, and sent notes across the form and thank-you page.
4. Test audio attachments and quota/error handling in the outbox, since they are the riskiest part of the offline interaction.
5. Keep the next change narrow: improve the server-side contract and browser validation around retries, rather than expanding the feature set again.

This is the next sensible improvement because the project has already demonstrated the core offline architecture. The remaining risk is correctness under real network loss, not the basic existence of the PWA scaffolding itself.

---

# PWQ Offline-First PWA Plan

## Prompt

> How to transform this progress web app (PWQ) an offline-first progressive web app (PWA)? First explain ELI10 what are the incremental steps to take to achieve the end goal. Store your response as a markdown file in the /docs file first. And then start generating the code for this after I approve your approach. Add this prompt also to the documentation file.

## Goal

Turn the existing Flask-rendered SayThanks/PWQ web app into an installable PWA that remains useful without a network connection, while keeping the server as the source of truth for authentication, inboxes, email notifications, and permanent note storage.

Offline-first does **not** mean that a browser can magically access PostgreSQL or send email without a connection. It means the app can open, show its useful shell, preserve user work, and queue work safely until the connection returns.

## ELI10 Explanation

Think of the app as a small notebook with a mail carrier:

1. **Give the app a name and a home-screen picture.** The manifest and icons let a phone install the app.
2. **Pack the important pages in the backpack.** A service worker saves the HTML shell, CSS, JavaScript, and images so the app can open offline.
3. **Save a note in the notebook first.** When someone writes a thank-you note, save the draft on the device immediately instead of risking losing it.
4. **Put unsent notes in an outbox.** If the internet is unavailable, mark the note as waiting rather than pretending it was delivered.
5. **Send the outbox when the mail carrier returns.** When the network comes back, retry queued notes and show whether each one succeeded or failed.
6. **Prevent duplicate letters.** Give each queued note an idempotency key so retries cannot create multiple notes on the server.
7. **Keep private information private.** Cache only public app assets and the user’s local drafts. Do not put Auth0 tokens, inbox data, or private notes into a shared offline cache.
8. **Test the important real-life situations.** Install it, turn on airplane mode, write a note, close the app, reopen it, reconnect, and verify that exactly one note arrives.

## Current Starting Point

- Flask renders the main pages through Jinja templates.
- `saythanks/templates/base.htm.j2` already references a web manifest and app icons.
- `saythanks/static/manifest.json` provides basic install metadata.
- There is currently no service-worker registration or service-worker file.
- Note submission in `saythanks/templates/submit_note.htm.j2` sends a multipart `XMLHttpRequest` directly to Flask.
- Notes, inboxes, authentication, and email delivery are server-side concerns backed by PostgreSQL, Auth0, and the email provider.
- Some assets are loaded from third-party CDNs, so a fully offline editor requires either locally hosted assets or an intentional offline fallback.

## Incremental Implementation Steps

### Phase 1: Define the offline contract

- Decide which screens must open offline: the public note form, a saved-draft view, and a small offline/status state.
- Decide which features remain online-only: login, private inbox browsing, inbox administration, and final delivery.
- Document the states shown to users: `draft`, `queued`, `sending`, `sent`, and `failed`.
- Decide how long local drafts and queued payloads are retained and how users delete them.

**Exit check:** a user can tell whether a note is saved locally, queued, delivered, or needs attention.

### Phase 2: Make the app installable

- Verify the manifest has a valid `scope`, `start_url`, `theme_color`, `background_color`, and complete icon set.
- Add a service-worker registration script to the shared base template.
- Add the required mobile metadata and a visible install/update status only where useful.
- Ensure the app is served over HTTPS in production; localhost is acceptable for development.

**Exit check:** Lighthouse or browser Application tools recognize the app as installable and the service worker registers successfully.

### Phase 3: Add safe asset and navigation caching

- Create a versioned service worker under the app’s static files.
- Pre-cache only the app shell and local static assets needed for the offline note experience.
- Use cache-first behavior for versioned static assets.
- Use network-first behavior for server-rendered HTML, with a deliberate offline fallback page when the network is unavailable.
- Never cache authenticated responses, form submissions, Auth0 responses, or arbitrary private inbox pages.
- Add cache cleanup when the service-worker version changes.

**Exit check:** after one online visit, the public note experience opens with DevTools set to Offline, without serving stale private data.

### Phase 4: Make note writing resilient

- Replace the current submit-only flow with a small client-side note model containing the recipient, topic, body, byline, and optional audio metadata.
- Store drafts in IndexedDB rather than `localStorage`, because IndexedDB handles structured records and larger payloads more reliably.
- Save on meaningful editor changes and before page unload where possible.
- Restore the latest draft for the same recipient/topic when the form opens.
- Keep the current direct submission behavior as the online fast path while the local draft is updated first.

**Exit check:** typing, refreshing, closing, and reopening the note form preserves the draft while online and offline.

### Phase 5: Add an outbox and synchronization

- On submit, create a local outbox record with a generated idempotency key and `queued` status.
- Attempt delivery immediately when online.
- Retry on `online`, app startup, and a user-visible retry action.
- Prefer Background Sync where supported, but never depend on it; the `online` event and next app launch are the fallback.
- Use exponential backoff and a retry limit for temporary failures.
- Keep permanent failures available for correction or deletion instead of retrying forever.
- Do not store sensitive authentication tokens in the outbox. Let the normal browser session/cookie and server authentication rules apply.

**Exit check:** a note submitted in airplane mode remains visible as queued, then is delivered once after reconnection.

### Phase 6: Make delivery idempotent on the server

- Add an idempotency key to the submission contract.
- Persist or otherwise safely recognize processed keys on the server.
- Return a stable success response when a retry repeats an already accepted key.
- Keep database insertion and notification behavior consistent when a request is retried.
- Add CSRF protection and validation to the new or updated submission path; do not weaken the existing protections.

**Exit check:** replaying the same queued request never creates duplicate notes or duplicate email notifications.

### Phase 7: Handle audio deliberately

- Offline audio is now supported for recorded or selected audio files. Store the Blob in IndexedDB and check browser storage limits and supported formats.
- Show a clear failure state when audio cannot be retained or uploaded.
- Remove local audio after confirmed delivery or explicit deletion.

**Exit check:** audio is either delivered exactly once or clearly reported as unavailable; it is never silently discarded.

### Phase 8: Privacy, limits, and recovery

- Add a local-data management action so users can delete drafts and queued notes from the device.
- Set retention and storage limits, and handle quota errors.
- Explain locally queued versus server-delivered status without exposing private data to other users of the device.
- Consider logout behavior carefully: local data should not be accidentally attached to another account or recipient.
- Provide a service-worker update path that does not strand users on an old shell.

**Exit check:** storage cleanup, logout, quota exhaustion, failed delivery, and service-worker upgrade have predictable outcomes.

### Phase 9: Test and release gradually

- Add JavaScript tests for draft persistence, queue transitions, retry behavior, and duplicate prevention.
- Add Flask tests for idempotency and validation.
- Add browser tests for install, offline navigation, offline draft recovery, reconnect, and one-time delivery.
- Run accessibility checks for status messaging and disabled/retry controls.
- Roll out offline audio with storage/quota monitoring, then consider richer inbox behavior.

## Recommended First Coding Slice

The first implementation should be deliberately small:

1. Add service-worker registration and an offline fallback.
2. Cache the public note-form shell and its local assets.
3. Add IndexedDB draft persistence for the note body and byline.
4. Add an offline status indicator and restore the draft after reload.
5. Do not queue or change server delivery until the draft behavior passes offline browser tests.

This slice proves the PWA foundation without mixing caching, authentication, database changes, email delivery, and audio handling in one change.

## Proposed File Areas

- `saythanks/templates/base.htm.j2`: manifest metadata and service-worker registration.
- `saythanks/templates/submit_note.htm.j2`: draft and outbox UI integration.
- `saythanks/static/js/`: browser storage, queue, and synchronization modules.
- `saythanks/static/service-worker.js`: cache and offline navigation policy.
- `saythanks/static/manifest.json`: install metadata.
- `saythanks/core.py`: service-worker/offline fallback routes only if Flask static serving cannot provide them directly.
- `tests/`: template, server idempotency, and browser-facing behavior coverage.

## Important Risks

- **Caching private pages:** a broad cache strategy could expose one user’s inbox on a shared device. Cache public assets only.
- **Duplicate delivery:** retries without idempotency can create duplicate notes and emails. Server-side protection is required.
- **Third-party editor/CDN assets:** the Toast UI editor and other remote assets are not reliably available offline. Bundle or locally serve the required editor assets before promising a fully offline editor.
- **Authentication expiry:** an offline browser cannot refresh an expired Auth0 session. Queueing must report an authentication failure and require an online retry.
- **Browser storage limits:** audio and large drafts may exceed quota. Handle quota errors visibly and remove stored audio after confirmed delivery.
- **Service-worker updates:** stale caches can leave users running old code. Use versioned caches and an explicit activation strategy.

## Questions and Responses

### What technology implements the outbox?

The outbox should be implemented with the browser's **IndexedDB** API. Each pending note is stored as a structured record containing its recipient, topic, body, byline, status, retry information, and a unique idempotency key. IndexedDB is preferable to `localStorage` because it supports structured data, larger payloads, asynchronous access, and optional audio Blobs.

The service worker is not the outbox itself. It can optionally use the **Background Sync API** to ask the browser to retry delivery when connectivity returns, but Background Sync is not available everywhere. The app must also retry on startup, on the browser's `online` event, and through a visible user action.

### Is IndexedDB built on SQLite?

Not directly. **IndexedDB is a browser-standard JavaScript storage API**, not a database engine such as SQLite. The browser decides how to implement it internally; different browsers and versions may use different storage engines, such as SQLite, LevelDB, or another internal system. Application code should use the IndexedDB API and must not depend on any particular underlying engine.

This also means the app does not need to install or manage SQLite for the PWA outbox. IndexedDB is provided by supported browsers and stores data locally within the browser's origin and storage rules.

### Can a user create more than one note while offline?

Yes. The user can create multiple independent text notes while offline. Each submission becomes its own IndexedDB outbox record with its own idempotency key and status. The records should remain separate so one failed note does not block or overwrite another.

When the connection returns, the app sends the queued notes individually, updates each record as `sending`, `sent`, or `failed`, and removes a record only after the server confirms successful delivery. The interface should show the number of queued notes and provide retry or delete controls for individual failures.

The first release supports multiple text notes and audio attachments offline. Audio depends on browser storage quota and is removed from the local outbox after confirmed delivery.

## Definition of Done

- The app can be installed on a supported browser over HTTPS.
- The public note experience opens after it has been visited once online.
- A text draft survives refresh and reopening while offline.
- Offline submission is visibly queued, never falsely reported as delivered, and can be retried.
- Reconnection delivers a queued note exactly once.
- Private inbox/authentication responses are not placed in the shared offline cache.
- Draft deletion, quota errors, authentication errors, service-worker updates, and permanent delivery failures have understandable UI states.
- Automated tests cover the browser storage/queue behavior and server idempotency contract.

## Approval Gate

No application code should be generated from this plan until the approach is approved. After approval, begin with the **Recommended First Coding Slice**, validate it in a real offline browser session, and then proceed phase by phase.