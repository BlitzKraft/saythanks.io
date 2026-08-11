# **Architecture & Implementation Documentation: Auth0 Login Refactoring** 

Related [PR](https://github.com/BlitzKraft/saythanks.io/pull/418) and issues ([397](https://github.com/BlitzKraft/saythanks.io/issues/397) and 
[439](https://github.com/BlitzKraft/saythanks.io/issues/439))

## **1. Our Moto & Architectural Philosophy** 

The core objective of this refactor is to solve five critical bugs (500 Server Crashes on duplicate nicknames, Ghost Users, Stale Emails, N+1 Query Inefficiency, and UI Desync) while adhering to **"Option A: Permanent Slugs."** 

**The Option A Philosophy:** When a user signs up for `saythanks.io` , their URL (e.g., `saythanks.io/to/sudarshan` ) hardcoded in GitHub READMEs, and shared on Twitter. If a user changes their GitHub username a year later, **we must not break their old saythanks URL** . Their identity is tied to their `auth_id` (a permanent unique identifier from Auth0), not their volatile GitHub `nickname` . Therefore, the system must recognize them via `auth_id` , silently update their email if needed, but permanently retain their original URL slug. 

## **2. Controller Refactoring (** **`core.py` )** 

### **The Original Code (Lines removed):** 

```
if not storage.Inbox.does_exist(nickname):
    storage.Inbox.store(nickname, userid, email)
```

- **The Flaw:** The controller was trying to orchestrate database logic based purely on the `nickname` . This caused the Ghost User bug and the 500 Server crashes. 

### **The New Code (Lines added):** 

```
final_slug = storage.Inbox.link_or_create(userid, nickname, email)
session['profile']['nickname'] = final_slug
```

### **Line-by-Line Breakdown:** 

##### **`final_slug = storage.Inbox.link_or_create(userid, nickname, email)`** 

- **Why this syntax?** We are delegating all complexity to the Data Access Layer ( `storage.py` ). The controller passes the raw identity tokens ( `userid` , `nickname` , `email` ) and expects exactly one thing back: the guaranteed, database-verified `final_slug` . 

- **Scenario:** If John logs in, the controller doesn't care if John is new or returning. It asks the database to figure it out and just tell the controller what URL to route John to. 

##### **`session['profile']['nickname'] = final_slug`** 

- **Why this syntax?** The `session` dictionary is what Flask uses to render the web UI (like the header at the top of the page). Previously, the UI blindly displayed whatever Auth0 sent. 

- **Scenario (The UI Desync Fix):** John signs up as `john` . Later, he changes his GitHub name to `john-dev` . Auth0 sends `john-dev` . Our database forces his slug to remain `john` (Option A). By explicitly overwriting `session['profile']['nickname'] =` 

`final_slug` , we guarantee the web UI says "Logged in as john", keeping the UI and Database perfectly synchronized. 

## **3. Data Layer Refactoring (** **`storage.py` )** 

### **The New Method:** **`link_or_create`** 

```
@classmethod
def link_or_create(cls, auth_id, nickname, email):
```

- **Why this syntax?** `@classmethod` is a Python decorator that allows us to call the method on the class itself ( `Inbox.link_or_create()` ) without having to instantiate an `Inbox` object first. We pass in `auth_id` as the primary key of identity. 

#### **_Part A: The Returning User Lookup_** 

```
q = sqlalchemy.text('SELECT slug, email FROM inboxes WHERE auth_id = :auth_id')
row = conn.execute(q, auth_id=auth_id).fetchone()
```

- **Why** **`.fetchone()` ?** Auth0 guarantees `auth_id` is unique. There can mathematically only be zero or one row. `.fetchone()` is faster than `.fetchall()` because it stops scanning after the first match. 

#### **_Part B: Handling the Returning User_** 

```
if row:
    existing_slug = row['slug']
    existing_email = row['email']
```

- **Logic:** If `row` is not empty, the user exists in our database. We extract their permanent slug and their historically saved email. 

```
    if existing_email != email:
        u = sqlalchemy.text('UPDATE inboxes SET email = :email WHERE auth_id
= :auth_id')
        conn.execute(u, email=email, auth_id=auth_id)
```

- **Why this syntax?** We compare the database email against the fresh Auth0 email. 

- **Scenario (Stale Email Fix):** Jane signed up in 2021 with `jane@college.edu` . In 2023, she changes her GitHub email to `jane@company.com` . If we don't update this, her saythanks email notifications will bounce. This block silently detects the mismatch and updates the database, guaranteeing email delivery. 

```
    return existing_slug
```

- **Why this syntax?** We immediately exit the function and return their original URL slug. 

- **Scenario:** Even if Auth0 says her name is now `jane-smith` , we return `jane` (her `existing_slug` ), enforcing our permanent links rule. 

#### **_Part C: Handling the New User (The Collision Loop)_** 

```
base_slug = nickname
slug_to_try = base_slug
```

```
counter = 1
```

- **Logic:** If `if row:` was false, this is a brand new user. We set up variables for our collision algorithm. 

```
while cls.does_exist(slug_to_try):
    slug_to_try = f"{base_slug}-{counter}"
    counter += 1
```

- **Why this syntax?** A `while` loop that continuously queries the database using the existing `does_exist` function until it finds a URL that is not taken. 

#####  **Scenario (The 500 Crash Fix):** 

   1. User A signs up with Google ( `john@gmail.com` ). Auth0 sends nickname `john` . Slug `john` is saved. 

   2. User B signs up with Google ( `john@yahoo.com` ). Auth0 sends nickname `john` . 

   3. User B hits the `while` loop. `does_exist('john')` is `True` . 

   4. The loop modifies the slug to `john-1` . 

   5. `does_exist('john-1')` is `False` . The loop breaks. 

- **Why it's necessary:** Without this loop, the database tries to insert a second `john` . Because the `slug` column has a `UNIQUE` constraint in the Postgres database, the database violently rejects it, throwing an `IntegrityError` and showing a 500 Server Error to User B. This loop elegantly prevents that crash. 

```
cls.store(slug_to_try, auth_id, email)
return slug_to_try
```

- **Why this syntax?** We finally call the existing `cls.store` method to perform the `INSERT` SQL statement, saving the brand new user to the database. We then return their newly minted, collision-free slug back to the controller. 

