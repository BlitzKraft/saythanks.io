# **Architecture & Implementation Documentation: Auth0 & Ngrok URL Refactoring**


## **1. Our Motto & Architectural Philosophy**

This refactor makes authentication and social-sharing URLs environment-aware. The previous implementation depended on hardcoded URLs such as `http://localhost:5000/callback` and `https://saythanks.io`. This breaks when the application is accessed through Ngrok or another external domain.

The goal is simple: **generate URLs from the current request environment instead of assuming one fixed domain.**

---

## **2. Auth0 Callback Refactoring (`core.py`)**

### **Original approach**

```python
auth_callback_url
```

- **The Flaw:** The callback URL came from a static `.env` value such as `http://localhost:5000/callback`.
- When a user accessed the application through Ngrok, Auth0 could redirect to localhost instead of the active Ngrok URL.

### **New approach**

```python
def get_callback_url():
    if request and hasattr(request, 'host') and ('ngrok' in request.host or 'localhost' not in request.host):
        return url_for('callback_handling', _external=True)
```

### **Line-by-Line Breakdown**

#### **`request.host`**

- Identifies the domain currently being used to access the application.

#### **`'ngrok' in request.host`**

- Detects an Ngrok environment.

#### **`'localhost' not in request.host`**

- Also supports externally accessible hosts that are not localhost.

#### **`url_for('callback_handling', _external=True)`**

- Generates a complete callback URL using the current host.

**Example:**

```text
https://alike-blizzard-docile.ngrok-free.dev/callback
```

instead of:

```text
http://localhost:5000/callback
```

### **Authentication Flow**

```text
User → Ngrok URL → Flask → get_callback_url()
     → Dynamic callback URL → Auth0 → Callback → Successful login
```

---

## **3. Social Sharing Refactoring (`share_note.htm.j2`)**

### **Problem**

The template contained hardcoded:

```text
https://saythanks.io
```

URLs.

When the application was running through Ngrok, the page could be served from the Ngrok domain while its sharing metadata still pointed to the production domain.

### **Solution**

```python
url_for(..., _external=True)
```

- Generates a complete URL using the current application/request context.
- Keeps note links, preview images, and social-sharing metadata aligned with the active domain.

**Example:**

```text
/note/12345
```

becomes:

```text
https://alike-blizzard-docile.ngrok-free.dev/note/12345
```

when `_external=True` is used.

---

## **4. Facebook Sharing Debugger Validation**

The **Facebook Sharing Debugger** was used to validate the social-sharing changes instead of directly connecting the application to Facebook.

### **Why it was used**

- The PR does not implement Facebook Login or a Facebook publishing/API integration.
- The requirement is to verify that Facebook can retrieve the shared page and correctly interpret its metadata.
- The debugger provides a practical way to inspect the shared URL, Open Graph title/description, preview image, and other sharing metadata.

### **Why direct Facebook integration was not needed**

Adding a Facebook API integration would introduce unnecessary dependencies and scope. The debugger is sufficient for validating the actual behavior that this PR changes.

```text
Application
    ↓
share_note.htm.j2
    ↓
Dynamic sharing URLs / metadata
    ↓
Facebook Sharing Debugger
    ↓
Validate Facebook's interpretation
```

### **Ngrok Validation**

A URL such as:

```text
https://alike-blizzard-docile.ngrok-free.dev/note/12345
```

can be submitted to the debugger to confirm that the externally generated URL and sharing metadata are accessible and correct.

---

## **5. How `core.py` Connects to `share_note.htm.j2`**

`core.py` is the controller and `share_note.htm.j2` is the presentation template.

```python
def share_note(uuid):
    ...
    return render_template('share_note.htm.j2', note=note)
```

- `core.py` receives the note UUID and retrieves the note from the database.
- `render_template()` passes the resulting `note` object to the Jinja template.
- The template uses values such as `{{ note.uuid }}` and generates environment-aware external URLs.

```text
Request → core.py → Database → note
                       ↓
             share_note.htm.j2
                       ↓
             Dynamic sharing URLs
```

---

## **6. Summary of Changes**

| Component | Change | Purpose |
|---|---|---|
| `core.py` | Added `get_callback_url()` | Dynamic Auth0 callback |
| `core.py` | `url_for(..., _external=True)` | Use current host |
| `share_note.htm.j2` | Removed hardcoded domain | Avoid incorrect sharing URLs |
| `share_note.htm.j2` | Dynamic external URLs | Correct Ngrok/production links |
| Facebook Sharing Debugger | Validation tool | Verify sharing metadata without Facebook API integration |

---

## **7. Expected Result**

### **Before**

```text
Ngrok → Auth0 → localhost callback → ❌ Login failure

Ngrok → hardcoded saythanks.io metadata → ❌ Wrong preview/link
```

### **After**

```text
Ngrok → dynamic callback → Auth0 → Ngrok callback → ✅ Login

Ngrok → dynamic sharing URLs → Debugger → ✅ Correct metadata
```

---

## **Conclusion**

This PR removes environment-specific URL assumptions from Auth0 authentication and note sharing.

Dynamic URL generation makes the application work correctly with Ngrok and other external hosts.

The Facebook Sharing Debugger is used only for validation, keeping the PR focused and avoiding unnecessary Facebook API integration.
