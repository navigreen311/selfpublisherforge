# SelfPublisherForge Chrome Extension

Amazon Research Assistant for self-publishers. Extract product data, track Best Sellers Rank (BSR), research niches, and save clips directly to your SelfPublisherForge account.

## Features

- **Product Data Extraction** -- Pull title, author, price, BSR, reviews, categories, keywords, ISBN, page count, and more from any Amazon product page.
- **BSR Tracking** -- Monitor Best Sellers Rank across categories with historical data and estimated daily sales.
- **Research Sidebar** -- In-page sidebar showing key metrics, BSR history, and related keywords without leaving Amazon.
- **Knowledge Vault Clips** -- Select text on any Amazon page and clip it to your SelfPublisherForge research vault.
- **Auto-Update Checks** -- Background update checks every 6 hours with notification support.
- **Offline Queue** -- Extractions made while offline are queued and automatically retried when connectivity returns.

## Supported Amazon Marketplaces

The extension works across **10 Amazon markets**:

| Marketplace | Domain |
|---|---|
| United States | amazon.com |
| United Kingdom | amazon.co.uk |
| Germany | amazon.de |
| France | amazon.fr |
| Canada | amazon.ca |
| Australia | amazon.com.au |
| Japan | amazon.co.jp |
| Italy | amazon.it |
| Spain | amazon.es |
| India | amazon.in |

## Development Setup

### Prerequisites

- Google Chrome (or a Chromium-based browser)
- A SelfPublisherForge account with an API token
- `bash`, `zip` (for the release script)

### Loading as an Unpacked Extension

1. Clone the repository and navigate to the `extension/` directory.
2. Open Chrome and go to `chrome://extensions`.
3. Enable **Developer mode** (toggle in the top-right corner).
4. Click **Load unpacked** and select the `extension/` directory.
5. The extension icon will appear in your toolbar. Click it to open the popup.
6. Enter your API URL (e.g., `https://api.selfpublisherforge.com`) and API token to connect.

### Project Structure

```
extension/
  background/
    service-worker.js    # Manifest V3 service worker: API client, auth, update checks, offline queue
  content/
    amazon-extractor.js  # Content script: DOM extraction for product data across all marketplaces
  icons/
    icon16.png           # Toolbar icon (16x16)
    icon48.png           # Extensions page icon (48x48)
    icon128.png          # Chrome Web Store / install icon (128x128)
    generate_icons.py    # Icon generation helper
  popup/
    popup.html           # Extension popup UI
    popup.js             # Popup logic: auth flow, quick actions
  scripts/
    prepare-release.sh   # Release automation script
  sidebar/
    sidebar.html         # Research sidebar UI
    sidebar.js           # Sidebar logic: metrics display, BSR history, keywords
  styles/
    popup.css            # Shared styles for popup and sidebar
  manifest.json          # Chrome extension manifest (Manifest V3)
  updates.xml            # Self-hosted auto-update manifest
```

## Release Process

### Using the Build Script

The `scripts/prepare-release.sh` script automates the entire release workflow:

```bash
cd extension/
./scripts/prepare-release.sh <EXTENSION_ID> <VERSION>
```

**Arguments:**

- `EXTENSION_ID` -- Your 32-character Chrome extension ID (lowercase letters a-p). Find this at `chrome://extensions` after loading the unpacked extension, or in the Chrome Web Store Developer Dashboard.
- `VERSION` -- Semantic version string (e.g., `1.2.0`).

**Example:**

```bash
./scripts/prepare-release.sh abcdefghijklmnopabcdefghijklmnop 1.2.0
```

**The script will:**

1. Validate the extension ID and version format.
2. Replace the `EXTENSION_ID` placeholder in `updates.xml` with your actual ID.
3. Update the `version` field in both `updates.xml` and `manifest.json`.
4. Create a zip archive at `extension/build/selfpublisherforge-v<VERSION>.zip`.
5. Print a summary with next steps.

### Manual Release Steps

If you prefer not to use the script:

1. Replace `EXTENSION_ID` in `updates.xml` with your actual Chrome extension ID.
2. Update the `version` in `updates.xml` and `manifest.json` to the new version.
3. Zip the extension directory (excluding `build/`, `scripts/`, `.git/`, `node_modules/`).
4. Upload the zip to the [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole).
5. If self-hosting, upload the signed `.crx` to your server.

### After Release

1. Test the update flow by verifying the installed version matches.
2. Commit and tag the release:
   ```bash
   git add -A
   git commit -m "Release v1.2.0"
   git tag v1.2.0
   git push origin main --tags
   ```

## Required Permissions

The extension requests the following permissions in `manifest.json`:

| Permission | Purpose |
|---|---|
| `activeTab` | Access the current tab to extract product data when the user clicks "Extract Page Data". |
| `storage` | Persist API credentials, pending extraction queue, and update check state across sessions. |
| `tabs` | Open new tabs for update notifications and detect Amazon product page navigation. |
| `sidePanel` | Display the research sidebar panel alongside Amazon pages. |
| `alarms` | Schedule periodic background tasks: update checks (every 6 hours) and extraction retries (every 5 minutes). |
| `notifications` | Show desktop notifications when a new extension version is available or a required update is needed. |

### Host Permissions

| Host Pattern | Purpose |
|---|---|
| `https://www.amazon.com/*` (and 9 other marketplaces) | Run the content script on Amazon product pages to extract data. |
| `https://api.selfpublisherforge.com/*` | Communicate with the SelfPublisherForge backend API. |
| `https://*.selfpublisherforge.com/*` | Support custom API deployments and the self-hosted update endpoint. |
