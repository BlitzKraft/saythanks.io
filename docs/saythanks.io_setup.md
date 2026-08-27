# Local Setup Guide: SayThanks.io with Auth0 and ngrok

## Purpose

This document provides a step-by-step guide to set up and run the
SayThanks.io application locally with Docker, Auth0, and ngrok.

The final setup allows the locally running website to be accessed
through a public HTTPS ngrok URL. This is required for testing features
such as Auth0 login, callback handling, and external services that
cannot access `localhost`.

------------------------------------------------------------------------

## Step 1 --- Clone the Repository

Clone the SayThanks.io repository and open the project directory.

Example:

``` powershell
git clone <repository-url>
cd <project-folder>
```

Verify that the project files are present:

``` powershell
Get-ChildItem
```

------------------------------------------------------------------------

## Step 2 --- Create the Local `conf` Folder

The repository uses `conf_template` as the configuration template.

Do **not** edit the template for your local credentials.

Create the local `conf` folder by copying the template:

``` powershell
Copy-Item -Recurse conf_template conf
```

After copying, the structure should be similar to:

``` text
project/
├── conf/
│   ├── db.env
│   ├── pgadmin.env
│   └── site.env
│
├── conf_template/
│   ├── db.env
│   ├── pgadmin.env
│   └── site.env
└── ...
```

### Important

-   `conf_template/` contains configuration templates intended to be
    committed.
-   `conf/` contains local configuration and should remain uncommitted
    if it contains secrets.
-   Do not overwrite an existing `conf/` folder unless you intentionally
    want to reset your local configuration.

------------------------------------------------------------------------

## Step 3 --- Install ngrok

On Windows, install ngrok using WinGet:

``` powershell
winget install ngrok.ngrok
```

Close and reopen PowerShell after installation.

Verify the installation:

``` powershell
ngrok version
```

You should see an ngrok version such as:

``` text
ngrok version 3.x.x
```

Verify the configuration:

``` powershell
ngrok config check
```


------------------------------------------------------------------------

## Step 4 --- Start the Docker Application

Make sure Docker is installed and running.

Check Docker:

``` powershell
docker --version
docker compose version
```

Confirm that the local configuration exists:

``` powershell
Get-ChildItem conf
```

Build and start the application:

``` powershell
docker compose up --build
```

Check the container status:

``` powershell
docker compose ps
```

The application and database containers should show a running status
such as `Up`.

Test the website locally:

``` text
http://127.0.0.1:5000
```

or:

``` text
http://localhost:5000
```

The website should load before continuing.

------------------------------------------------------------------------

## Step 5 --- Start ngrok

Keep Docker running.

Open a **new PowerShell terminal** and run:

``` powershell
ngrok http 127.0.0.1:5000
```

ngrok should display a forwarding address similar to:

``` text
Forwarding    https://example.ngrok-free.dev -> http://127.0.0.1:5000
```

Copy only the public HTTPS URL:

``` text
https://example.ngrok-free.dev
```

Keep this ngrok terminal running.

Test the public URL in a browser:

``` text
https://example.ngrok-free.dev
```

It should reach the same local SayThanks.io application.

------------------------------------------------------------------------

## Step 6 --- Create `AUTH0_CALLBACK_URL`

The Auth0 callback URL is created from the ngrok URL.

If ngrok provides:

``` text
https://example.ngrok-free.dev
```

add `/callback`:

``` text
https://example.ngrok-free.dev/callback
```

Open:

``` text
conf/site.env
```

Edit the local configuration file, not the template.

Set:

``` env
AUTH0_CALLBACK_URL='https://example.ngrok-free.dev/callback'
```

Use your actual ngrok URL.

### Important

Do not use:

``` text
http://127.0.0.1:5000/callback
```

for the ngrok-based Auth0 setup.

The callback URL must use the current public HTTPS ngrok URL.

------------------------------------------------------------------------

## Step 7 --- Add the Callback URL to Auth0

Open the Auth0 Dashboard:

https://manage.auth0.com/

Navigate to:

**Applications → Applications → SayThanks application → Settings**

Scroll to:

**Application URIs → Allowed Callback URLs**

Add the exact callback URL from Step 6.

Example:

``` text
https://example.ngrok-free.dev/callback
```

Click:

**Save Changes**

### Important

The following two values must match exactly:

`conf/site.env`:

``` env
AUTH0_CALLBACK_URL='https://example.ngrok-free.dev/callback'
```

Auth0:

``` text
Allowed Callback URLs
https://example.ngrok-free.dev/callback
```

Differences in protocol, domain, path, port, or trailing slash can cause
a callback URL mismatch.

------------------------------------------------------------------------

## Step 8 --- Get Auth0 Domain, Client ID, and Client Secret

Remain in the same Auth0 application.

Navigate to:

**Applications → Applications → SayThanks application → Settings**

Copy these three values:

### AUTH0_DOMAIN

Find **Domain** and copy it.

Add it to:

``` env
AUTH0_DOMAIN='your-auth0-domain'
```

### AUTH0_CLIENT_ID

Find **Client ID** and copy it.

Add it to:

``` env
AUTH0_CLIENT_ID='your-client-id'
```

### AUTH0_CLIENT_SECRET

Find **Client Secret** and copy it.

Add it to:

``` env
AUTH0_CLIENT_SECRET='your-client-secret'
```

Do not share or commit the Client Secret.

------------------------------------------------------------------------

## Step 9 --- Get `AUTH0_JWT_V2_TOKEN`

This value is a Management API access token.

In the Auth0 Dashboard, navigate to:

**Applications → APIs → Auth0 Management API → API Explorer**

Follow this exact path in the Auth0 Dashboard sidebar:

``` text
Applications (sidebar)
   → APIs
      → Auth0 Management API   (card labeled "System API")
         → API Explorer tab
            → Token field
```

Step by step:

1. In the left sidebar, click **Applications** to expand it.
2. Click **APIs** (a sub-item under Applications).
3. On the APIs page, click the card named **Auth0 Management API**.
4. On the Management API page, click the **API Explorer** tab (it's
   next to Quickstart, Settings, Permissions, Application Access, Test).
5. Under **Token**, you'll see a long masked string of characters. Click
   the **eye icon** to reveal it, or the **copy icon** next to it to
   copy it directly.

Find the **Token** section.

Copy the generated Management API token.

Open:

``` text
conf/site.env
```

Add:

``` env
AUTH0_JWT_V2_TOKEN='your-management-api-token'
```

Use the actual token from Auth0.

### Security

Treat this token as a secret.

Do not:

-   Commit it to Git.
-   Add it to a pull request.
-   Post it in an issue.
-   Share it in screenshots.
-   Send it publicly.

The token must have the permissions required by the application's
Management API operations.

------------------------------------------------------------------------

## Step 10 --- Verify `conf/site.env`

Before restarting Docker, verify that all five Auth0 variables are
present.

Your local `conf/site.env` should contain values similar to:

``` env
AUTH0_DOMAIN='your-auth0-domain'

AUTH0_CLIENT_ID='your-client-id'

AUTH0_CLIENT_SECRET='your-client-secret'

AUTH0_CALLBACK_URL='https://example.ngrok-free.dev/callback'

AUTH0_JWT_V2_TOKEN='your-management-api-token'
```

Use your real values instead of the examples.

### Verify Git Ignore

Run:

``` powershell
git check-ignore -v conf/site.env
```

If the file is ignored by Git, it should not appear as a file to commit.

Check the repository status:

``` powershell
git status
```

Do not run:

``` powershell
git add conf/site.env
```

The file contains sensitive credentials.

------------------------------------------------------------------------

## Step 11 --- Restart Docker and Test the Application

Keep the ngrok terminal running.

Open another PowerShell terminal in the project directory.

Stop the containers:

``` powershell
docker compose down
```

Start them again:

``` powershell
docker compose up -d
```

Check their status:

``` powershell
docker compose ps
```

The required containers should be running.

### Test locally

Open:

``` text
http://127.0.0.1:5000
```

Confirm that the website loads.

### Test through ngrok

Open:

``` text
https://YOUR-NGROK-DOMAIN.ngrok-free.dev
```

Click the application's login option.

The expected flow is:

``` text
Browser
   ↓
ngrok HTTPS URL
   ↓
SayThanks.io
   ↓
Auth0 Login
   ↓
Successful authentication
   ↓
/callback
   ↓
Logged-in application
```

------------------------------------------------------------------------

# Final Confirmation --- Local and Network Tunnel Setup

After completing Steps 1--11, the complete architecture is:

``` text
                         Internet
                            │
                            ▼
              https://YOUR-NGROK-URL
                            │
                            ▼
                         ngrok
                            │
                            ▼
                  127.0.0.1:5000
                            │
                            ▼
                    SayThanks.io
                     /          \
                    /            \
                 Auth0        PostgreSQL
                 Login          :5432
```

The ngrok tunnel exposes the **web application running on port 5000** to
the internet.

Therefore, features that use the SayThanks.io backend can be tested
through the public ngrok URL, including:

-   Website pages
-   Auth0 login
-   Auth0 callback
-   Application forms and requests
-   Message-related application functionality
-   Database-backed operations
-   External services that need to access the public application URL
-   Social-sharing URL testing

The PostgreSQL database does **not** need to be exposed through ngrok.
It remains local and is accessed by the application.

### Final Verification Checklist

-   [ ] Repository cloned successfully
-   [ ] `conf/` created from `conf_template/`
-   [ ] ngrok installed and authenticated
-   [ ] Docker containers running
-   [ ] Website accessible at `localhost:5000`
-   [ ] ngrok tunnel running
-   [ ] Public ngrok HTTPS URL accessible
-   [ ] `AUTH0_CALLBACK_URL` configured in `conf/site.env`
-   [ ] Same callback URL added to Auth0
-   [ ] Auth0 Domain configured
-   [ ] Auth0 Client ID configured
-   [ ] Auth0 Client Secret configured
-   [ ] Auth0 Management API token configured
-   [ ] `conf/site.env` is not tracked by Git
-   [ ] Docker restarted after configuration
-   [ ] Auth0 login tested successfully
-   [ ] Website tested through the ngrok URL
-   [ ] Message/application functionality tested through the ngrok URL

## Important Operational Note

The free ngrok URL may change when the tunnel is restarted. If the URL
changes, update both:

``` text
conf/site.env
```

and:

``` text
Auth0 → Application → Settings → Allowed Callback URLs
```

with the new callback URL.

Keep the ngrok terminal running while testing the public website. If
ngrok is stopped, the public tunnel will no longer be available.

## Setup Complete

If the website loads through the ngrok HTTPS URL and Auth0 login
successfully redirects to `/callback` and returns to the application,
the local Docker + Auth0 + ngrok environment is configured successfully.
