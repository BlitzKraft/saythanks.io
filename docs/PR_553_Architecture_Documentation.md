# **Architecture & Implementation Documentation: Offline Message Creation & Auto-Sync Refactoring**

Related issue: [#553](https://github.com/BlitzKraft/saythanks.io/issues/553) ("Creation of saythanks message when offline is not working")

---

## **1. Our Motto & Architectural Philosophy**

**The Offline-First Philosophy:** A core promise of Progressive Web Apps (PWAs) is that user activity—specifically composing and submitting a thank-you note—must **never be lost due to network unavailability**. Whether a user is on a mobile device with poor connectivity or intentionally offline in Airplane Mode, typing a message at `saythanks.io/to/<inbox>` must allow seamless composition, store the note locally in an offline outbox (IndexedDB), and automatically background-sync the payload to the PostgreSQL database once connectivity returns.

### **Root Causes Addressed in Issue #553:**

1. **CDN Hard Dependency:** The rich-text editor (`Toast UI Editor`) loaded scripts and CSS via external `uicdn.toast.com` links. When offline, the editor failed to load entirely, preventing note composition.
2. **Fatal JavaScript Syntax Error:** A duplicate `let audioBlob` declaration broke strict-mode script execution, disabling the client-side IndexedDB database and service worker event listeners.
3. **Missing Network Error Interception:** On network failures (`request.onerror`), the client printed "Network error." without saving the note to the offline queue.
4. **Backend Server 500 Crashes (SQLAlchemy 2.x Incompatibility):** When offline notes auto-synced back online, raw database query executions in `storage.py` failed due to SQLAlchemy 2.x positional keyword parameter deprecations.

---

## **2. Frontend & Template Refactoring (`submit_note.htm.j2`)**

### **A. Toast UI Local Asset Bundling**

#### **Original Code (Lines removed):**

```html
<script src="https://uicdn.toast.com/editor/latest/toastui-editor-all.min.js"></script>
<link
  rel="stylesheet"
  href="https://uicdn.toast.com/editor/latest/toastui-editor.min.css"
/>
```

#### **New Code (Lines added):**

```html
<script src="{{ url_for('static', filename='toastui-editor-all.min.js') }}"></script>
<link
  rel="stylesheet"
  href="{{ url_for('static', filename='toastui-editor.min.css') }}"
/>
```

- **Why this syntax?** Bundling `toastui-editor-all.min.js` and `toastui-editor.min.css` directly in `saythanks/static/` guarantees the editor loads completely from local Flask static assets / Service Worker cache when offline.

---

### **B. Script Syntax Error & Scope Clean-up**

#### **Original Code:**

```javascript
// Scope 1
let audioBlob;
...
// Scope 2 (Voice Recording Script)
let audioBlob;
```

#### **New Code:**

```javascript
// Top-level initialization
let audioBlob = null;
...
// Re-use initialized variable without re-declaring `let`
```

- **Why this syntax?** In JavaScript strict mode, duplicate `let` declarations in the same scope throw `Uncaught SyntaxError: Identifier 'audioBlob' has already been declared`. Fixing this allows all client-side scripts and IndexedDB initializations to run cleanly.

---

### **C. Automatic Network Fallback to IndexedDB (`request.onerror`)**

#### **Original Code:**

```javascript
request.onerror = () => {
  submitBtn.disabled = false;
  recordingStatus.innerText = "Network error.";
};
```

#### **New Code:**

```javascript
request.onerror = () => {
  queueOfflineNote()
    .then(() => {
      window.location.href = "/thanks?status=queued";
    })
    .catch((queueError) => {
      submitBtn.disabled = false;
      outboxStatus.textContent =
        "Could not reach the server and offline queuing also failed.";
      console.error("queueOfflineNote failed:", queueError);
    });
};
```

- **Why this syntax?** On network loss or request drop, `request.onerror` automatically intercepts the failure, calls `queueOfflineNote()` to persist the message to IndexedDB, and redirects the user to `/thanks?status=queued`.

---

## **3. Data Layer Refactoring (`storage.py`)**

To handle auto-synced notes from reconnecting clients, database queries across `storage.py` were refactored for **SQLAlchemy 2.x compatibility**.

### **Line-by-Line Breakdown:**

#### **A. Passing Parameters as Dictionaries**

##### **Original Code:**

```python
r = conn.execute(q, slug=slug).fetchall()
```

##### **New Code:**

```python
r = conn.execute(q, {"slug": slug}).fetchall()
```

- **Why this syntax?** SQLAlchemy 2.x removed positional keyword parameters (`slug=slug`). Passing dictionary parameters `{"slug": slug}` prevents Python `TypeError` exceptions.

#### **B. Dual-Compatible `row_dict()` for SQLAlchemy 1.x & 2.x Row Result Access**

##### **Helper Implementation:**

```python
def row_dict(row):
    """Safely return a dictionary-like row interface for both SQLAlchemy 1.x and 2.x."""
    if row is None:
        return None
    return row._mapping if hasattr(row, '_mapping') else row
```

##### **Column Access Usage:**

```python
return row_dict(r[0])['email']
```

- **Why this syntax?** 
  - **SQLAlchemy 1.x (Production server, Python 3.6):** Query result rows (`RowProxy`) do not possess a `._mapping` attribute; column values are accessed via standard key lookup `row['column']`. Calling `row._mapping` triggers `AttributeError: Could not locate column in row for column '_mapping'`.
  - **SQLAlchemy 2.x (Modern local Docker, Python 3.10+):** `Row` objects removed string key indexing and require `row._mapping['column']`.
  - **The Solution:** The `row_dict()` helper dynamically inspects whether `_mapping` exists on the row. If present (SQLAlchemy 2.x), it returns `row._mapping`; otherwise (SQLAlchemy 1.x), it returns `row` directly. This guarantees 100% backward and forward compatibility across both environments.

---

## **4. PWA Service Worker & Offline Caching (`service-worker.js`)**

- Registered static editor dependencies (`toastui-editor-all.min.js`, `toastui-editor.min.css`) in the Service Worker pre-cache list.
- Verified background sync outbox listener for auto-flushing queued notes when the `online` event fires.
