/**
 * popup.js — Extension popup logic.
 *
 * Handles auth-check, connect/disconnect, and quick-action buttons that
 * communicate with the background service worker.
 */

// DOM references
const loginSection = document.getElementById("login-section");
const actionsSection = document.getElementById("actions-section");
const authStatus = document.getElementById("auth-status");
const apiUrlInput = document.getElementById("api-url");
const apiTokenInput = document.getElementById("api-token");
const btnConnect = document.getElementById("btn-connect");
const btnExtract = document.getElementById("btn-extract");
const btnSidebar = document.getElementById("btn-sidebar");
const btnClip = document.getElementById("btn-clip");
const btnDisconnect = document.getElementById("btn-disconnect");
const extractResult = document.getElementById("extract-result");
const versionLabel = document.getElementById("version-label");
const updateBadge = document.getElementById("update-badge");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function showLogin() {
  loginSection.classList.remove("hidden");
  actionsSection.classList.add("hidden");
  authStatus.textContent = "Disconnected";
  authStatus.classList.remove("auth-badge--connected");
  authStatus.classList.add("auth-badge--disconnected");
}

function showActions() {
  loginSection.classList.add("hidden");
  actionsSection.classList.remove("hidden");
  authStatus.textContent = "Connected";
  authStatus.classList.remove("auth-badge--disconnected");
  authStatus.classList.add("auth-badge--connected");
}

function showResult(text, isError = false) {
  extractResult.textContent = text;
  extractResult.classList.remove("hidden", "result-box--error", "result-box--success");
  extractResult.classList.add(isError ? "result-box--error" : "result-box--success");
}

/**
 * Send a message to the background service worker and await a response.
 */
function sendMessage(action, payload = {}) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage({ action, ...payload }, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(response);
      }
    });
  });
}

// ---------------------------------------------------------------------------
// Initialise — check stored auth on popup open
// ---------------------------------------------------------------------------

async function init() {
  // Display the version dynamically from the manifest
  const manifest = chrome.runtime.getManifest();
  if (versionLabel) {
    versionLabel.textContent = `SelfPublisherForge v${manifest.version}`;
  }

  try {
    const { apiUrl, apiToken, updateAvailable } =
      await chrome.storage.local.get(["apiUrl", "apiToken", "updateAvailable"]);

    if (apiUrl && apiToken) {
      apiUrlInput.value = apiUrl;
      showActions();
    } else {
      showLogin();
    }

    // Show / hide the update badge based on stored flag
    if (updateAvailable && updateBadge) {
      updateBadge.classList.remove("hidden");
    }
  } catch {
    showLogin();
  }
}

// ---------------------------------------------------------------------------
// Connect
// ---------------------------------------------------------------------------

btnConnect.addEventListener("click", async () => {
  const apiUrl = apiUrlInput.value.trim().replace(/\/+$/, "");
  const apiToken = apiTokenInput.value.trim();

  if (!apiUrl || !apiToken) {
    alert("Please enter both API URL and token.");
    return;
  }

  // Validate API URL format
  if (!apiUrl.startsWith("https://")) {
    alert("API URL must start with https://");
    return;
  }
  try {
    new URL(apiUrl);
  } catch {
    alert("API URL is not a valid URL.");
    return;
  }

  // Validate API token length
  if (apiToken.length < 1 || apiToken.length > 500) {
    alert("API token must be between 1 and 500 characters.");
    return;
  }

  btnConnect.disabled = true;
  btnConnect.textContent = "Connecting...";

  try {
    await chrome.storage.local.set({ apiUrl, apiToken });
    // Verify connection with a quick health check via background
    const res = await sendMessage("healthCheck");
    if (res && res.success) {
      showActions();
    } else {
      showResult("Connection failed. Check your URL and token.", true);
      showLogin();
    }
  } catch (err) {
    showResult(`Error: ${err.message}`, true);
    showLogin();
  } finally {
    btnConnect.disabled = false;
    btnConnect.textContent = "Connect";
  }
});

// ---------------------------------------------------------------------------
// Extract page data
// ---------------------------------------------------------------------------

btnExtract.addEventListener("click", async () => {
  btnExtract.disabled = true;
  btnExtract.textContent = "Extracting...";

  try {
    // Ask the content script to extract data from the active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) {
      showResult("No active tab found.", true);
      return;
    }

    const extractionResult = await chrome.tabs.sendMessage(tab.id, {
      action: "extractData",
    });

    if (!extractionResult || !extractionResult.data) {
      showResult("Could not extract data. Is this an Amazon product page?", true);
      return;
    }

    // Send to backend via background service worker
    const saveResult = await sendMessage("saveExtraction", {
      data: extractionResult.data,
    });

    if (saveResult && saveResult.success) {
      showResult(
        `Saved: ${extractionResult.data.title || "Product"} (ASIN: ${extractionResult.data.asin})`
      );
    } else {
      showResult(`Save failed: ${saveResult?.error || "Unknown error"}`, true);
    }
  } catch (err) {
    showResult(`Error: ${err.message}`, true);
  } finally {
    btnExtract.disabled = false;
    btnExtract.textContent = "Extract Page Data";
  }
});

// ---------------------------------------------------------------------------
// Open research sidebar
// ---------------------------------------------------------------------------

btnSidebar.addEventListener("click", async () => {
  try {
    // Open the side panel (Manifest V3 side_panel API)
    if (chrome.sidePanel) {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab) {
        await chrome.sidePanel.open({ tabId: tab.id });
      }
    } else {
      // Fallback: inject sidebar as an iframe overlay via content script
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (tab) {
        await chrome.tabs.sendMessage(tab.id, { action: "toggleSidebar" });
      }
    }
  } catch (err) {
    showResult(`Could not open sidebar: ${err.message}`, true);
  }
});

// ---------------------------------------------------------------------------
// Clip selection to Knowledge Vault
// ---------------------------------------------------------------------------

btnClip.addEventListener("click", async () => {
  btnClip.disabled = true;
  btnClip.textContent = "Clipping...";

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) {
      showResult("No active tab found.", true);
      return;
    }

    // Get selected text from content script
    const selectionResult = await chrome.tabs.sendMessage(tab.id, {
      action: "getSelection",
    });

    const selectedText = selectionResult?.text;
    if (!selectedText) {
      showResult("No text selected on the page.", true);
      return;
    }

    const saveResult = await sendMessage("saveClip", {
      clip: {
        clip_type: "text",
        content: selectedText,
        source_url: tab.url,
        title: tab.title,
        tags: [],
      },
    });

    if (saveResult && saveResult.success) {
      showResult("Clip saved to Knowledge Vault!");
    } else {
      showResult(`Save failed: ${saveResult?.error || "Unknown error"}`, true);
    }
  } catch (err) {
    showResult(`Error: ${err.message}`, true);
  } finally {
    btnClip.disabled = false;
    btnClip.textContent = "Clip Selection to Vault";
  }
});

// ---------------------------------------------------------------------------
// Disconnect
// ---------------------------------------------------------------------------

btnDisconnect.addEventListener("click", async () => {
  await chrome.storage.local.remove(["apiUrl", "apiToken"]);
  showLogin();
});

// ---------------------------------------------------------------------------
// Update badge click — open the update URL
// ---------------------------------------------------------------------------

if (updateBadge) {
  updateBadge.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      const { apiUrl } = await chrome.storage.local.get(["apiUrl"]);
      if (apiUrl) {
        const response = await fetch(
          `${apiUrl}/api/v1/extension/version`
        );
        if (response.ok) {
          const json = await response.json();
          const remote = json.data || json;
          chrome.tabs.create({ url: remote.update_url });
          return;
        }
      }
    } catch {
      // ignore — fall through to default
    }
    // Fallback URL
    chrome.tabs.create({
      url: "https://selfpublisherforge.com/extension/updates.xml",
    });
  });
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", init);
