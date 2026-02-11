# OAuth Provider Setup Guide

This guide walks through configuring Google and GitHub as OAuth login providers for SelfPublisherForge. OAuth is **optional** -- email/password authentication works without it.

---

## Table of Contents

- [Overview](#overview)
- [Google OAuth Setup](#google-oauth-setup)
- [GitHub OAuth Setup](#github-oauth-setup)
- [Environment Variables Reference](#environment-variables-reference)
- [Redirect URI Format](#redirect-uri-format)
- [Troubleshooting](#troubleshooting)
- [Style Cloning Feature Word Lists](#style-cloning-feature-word-lists)

---

## Overview

SelfPublisherForge supports social login through **Google** and **GitHub** OAuth. When configured, users can sign in with their existing accounts instead of creating a new email/password credential.

**How it works:**

1. The frontend redirects the user to the provider's authorization page.
2. The user grants consent and is redirected back to the application with an authorization code.
3. The backend exchanges the code for an access token, fetches the user's profile, and creates or links a local account.
4. The backend issues JWT tokens and the user is logged in.

**When OAuth is not configured**, the backend returns HTTP 501 for OAuth-related endpoints. The frontend should hide the "Sign in with Google/GitHub" buttons when the corresponding client IDs are empty.

---

## Google OAuth Setup

### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown at the top and select **New Project**.
3. Enter a project name (e.g., "SelfPublisherForge") and click **Create**.
4. Select the newly created project.

### Step 2: Enable Required APIs

1. Navigate to **APIs & Services > Library**.
2. Search for and enable the following APIs:
   - **Google+ API** (or **Google People API**)
   - **Google Identity Services**

### Step 3: Configure the OAuth Consent Screen

1. Navigate to **APIs & Services > OAuth consent screen**.
2. Select **External** as the user type (unless your org uses Google Workspace and you want internal-only access).
3. Fill in the required fields:
   - **App name**: SelfPublisherForge
   - **User support email**: your email address
   - **Developer contact email**: your email address
4. Under **Scopes**, add:
   - `openid`
   - `email`
   - `profile`
5. Save and continue through the remaining steps.
6. If you are in testing mode, add your test user email addresses under **Test users**.

### Step 4: Create OAuth 2.0 Credentials

1. Navigate to **APIs & Services > Credentials**.
2. Click **Create Credentials > OAuth client ID**.
3. Select **Web application** as the application type.
4. Set the **Name** (e.g., "SelfPublisherForge Web Client").
5. Under **Authorized JavaScript origins**, add:
   - `http://localhost:3000` (development)
   - `https://your-domain.com` (production)
6. Under **Authorized redirect URIs**, add:
   - `http://localhost:3000/auth/google/callback` (development)
   - `https://your-domain.com/auth/google/callback` (production)
7. Click **Create**.
8. Copy the **Client ID** and **Client Secret**.

### Step 5: Configure Environment Variables

Add the following to your `.env` file:

```env
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
```

---

## GitHub OAuth Setup

### Step 1: Register a New OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers).
   - For organization-owned apps, go to **Organization Settings > Developer settings > OAuth Apps**.
2. Click **New OAuth App** (or **Register a new application**).

### Step 2: Fill in Application Details

- **Application name**: SelfPublisherForge
- **Homepage URL**: `http://localhost:3000` (development) or `https://your-domain.com` (production)
- **Authorization callback URL**: `http://localhost:3000/auth/github/callback`
  - You can only set **one** callback URL per OAuth App. For production, create a separate OAuth App or update this value when deploying.

### Step 3: Get Client ID and Secret

1. After creating the app, you will see the **Client ID** on the app's settings page.
2. Click **Generate a new client secret**.
3. Copy the secret immediately -- it is only shown once. If you lose it, generate a new one.

### Step 4: Configure Environment Variables

Add the following to your `.env` file:

```env
GITHUB_CLIENT_ID=Iv1.abcdef1234567890
GITHUB_CLIENT_SECRET=abcdef1234567890abcdef1234567890abcdef12
GITHUB_REDIRECT_URI=http://localhost:3000/auth/github/callback
```

### Note on GitHub Email Access

GitHub OAuth requests the `read:user` and `user:email` scopes. If the user's email is not publicly visible on their GitHub profile, the backend fetches it from the `/user/emails` endpoint. The backend prefers the **primary, verified** email address.

Users with no verified email on their GitHub account will receive an error and cannot sign in via GitHub OAuth.

---

## Environment Variables Reference

| Variable                 | Required | Description                                           |
|--------------------------|----------|-------------------------------------------------------|
| `GOOGLE_CLIENT_ID`       | No       | Google OAuth 2.0 client ID                            |
| `GOOGLE_CLIENT_SECRET`   | No       | Google OAuth 2.0 client secret                        |
| `GOOGLE_REDIRECT_URI`    | No       | Redirect URI registered in Google Cloud Console       |
| `GITHUB_CLIENT_ID`       | No       | GitHub OAuth App client ID                            |
| `GITHUB_CLIENT_SECRET`   | No       | GitHub OAuth App client secret                        |
| `GITHUB_REDIRECT_URI`    | No       | Redirect URI registered in GitHub OAuth App settings  |

All OAuth variables default to empty strings. When empty, the corresponding provider is disabled and the backend returns HTTP 501 for that provider's endpoints.

In production, these are classified as `[RECOMMENDED]` -- the app will start without them, but a warning is logged to remind you that OAuth login is unavailable.

---

## Redirect URI Format

The redirect URI is the URL that the OAuth provider sends the user back to after authorization. It must **exactly match** the URI registered with the provider.

**Pattern:**

```
https://your-domain.com/auth/{provider}/callback
```

**Examples:**

| Environment | Provider | Redirect URI                                           |
|-------------|----------|--------------------------------------------------------|
| Development | Google   | `http://localhost:3000/auth/google/callback`            |
| Development | GitHub   | `http://localhost:3000/auth/github/callback`            |
| Production  | Google   | `https://your-domain.com/auth/google/callback`          |
| Production  | GitHub   | `https://your-domain.com/auth/github/callback`          |

**Important:** The redirect URI in your `.env` file, the URI registered with the OAuth provider, and the URI your frontend redirects to must all be identical. A mismatch causes a `redirect_uri_mismatch` error.

---

## Troubleshooting

### "Google OAuth is not configured" / "GitHub OAuth is not configured" (HTTP 501)

**Cause:** The `GOOGLE_CLIENT_ID` or `GITHUB_CLIENT_ID` environment variable is empty or not set.

**Fix:** Set the corresponding client ID and client secret in your `.env` file. Restart the backend.

---

### `redirect_uri_mismatch` Error from Google

**Cause:** The `GOOGLE_REDIRECT_URI` in your `.env` file does not exactly match one of the **Authorized redirect URIs** in the Google Cloud Console.

**Fix:**
1. Go to [Google Cloud Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials).
2. Click on your OAuth 2.0 client.
3. Verify that the redirect URI matches exactly (including protocol, host, port, and path).
4. Common mistakes:
   - Trailing slash mismatch (`/callback` vs. `/callback/`)
   - `http` vs. `https`
   - Wrong port number

---

### `redirect_uri_mismatch` Error from GitHub

**Cause:** The `GITHUB_REDIRECT_URI` in your `.env` file does not match the **Authorization callback URL** in your GitHub OAuth App settings.

**Fix:**
1. Go to [GitHub Developer Settings > OAuth Apps](https://github.com/settings/developers).
2. Click on your app.
3. Verify the **Authorization callback URL** matches your `GITHUB_REDIRECT_URI` exactly.

---

### "GitHub account does not have a verified email address" (HTTP 400)

**Cause:** The user's GitHub account has no verified email address, or their email privacy settings prevent access.

**Fix:** The user needs to:
1. Go to [GitHub > Settings > Emails](https://github.com/settings/emails).
2. Add and verify at least one email address.
3. Ensure "Keep my email addresses private" does not block all emails (the `user:email` scope requests access regardless of this setting, but the email must be verified).

---

### OAuth Login Creates a New Account Instead of Linking

**Cause:** The email address from the OAuth provider does not match the email of an existing SelfPublisherForge account.

**Fix:** This is expected behavior. The system links OAuth accounts to existing users by matching email addresses. If the OAuth email differs from the registered email, a new account is created. To link accounts, the user should ensure they use the same email address for both their SelfPublisherForge account and their OAuth provider.

---

### "Failed to exchange authorization code for tokens" (HTTP 401)

**Cause:** The authorization code has expired, was already used, or the client secret is incorrect.

**Fix:**
1. Verify your client secret is correct and has not been regenerated.
2. Authorization codes are single-use and short-lived (typically 10 minutes). Do not retry with the same code.
3. For Google: ensure the client secret in `.env` matches the one in Cloud Console.
4. For GitHub: client secrets can only be viewed once. If lost, generate a new one.

---

### CORS Errors During OAuth Flow

**Cause:** The frontend origin is not included in `CORS_ORIGINS`.

**Fix:** Ensure `FRONTEND_URL` in your `.env` matches the origin of your frontend application. The backend automatically appends `FRONTEND_URL` to the `CORS_ORIGINS` list at startup.

---

### OAuth Works in Development but Not in Production

**Common causes:**
1. **Redirect URI not updated** -- production uses `https://your-domain.com` but the OAuth provider still has `http://localhost:3000` registered.
2. **Missing production redirect URI** -- add the production URL to the provider's allowed redirect URIs.
3. **Google consent screen in testing mode** -- publish the consent screen or add test users.
4. **GitHub OAuth App has only one callback URL** -- create a separate OAuth App for production, or update the callback URL.

---

## Style Cloning Feature Word Lists

The style cloning module uses word lists for linguistic feature extraction (stop words, transition words, emotional words). These lists have hardcoded defaults in the codebase but can be customized.

**To customize the word lists:**

1. Create a JSON file at `backend/app/modules/style_cloning/feature_words.json`.
2. Include any or all of the following keys:

```json
{
  "stop_words": ["the", "be", "to", "of", "and", "..."],
  "transition_words": ["however", "moreover", "furthermore", "..."],
  "emotional_words": ["love", "hate", "fear", "anger", "joy", "..."]
}
```

3. Any key not present in the JSON file falls back to the hardcoded default list.
4. Restart the backend for changes to take effect (word lists are loaded at module import time).

This is a low-priority configuration option. The hardcoded defaults cover standard English and are suitable for most use cases.
