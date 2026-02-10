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
const statusMessage = document.getElementById("status-message");
const loadingSpinner = document.getElementById("loading-spinner");

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
 * Show a status message to the user (success or error).
 */
function showStatusMessage(text, isError = false) {
  if (!statusMessage) return;
  statusMessage.textContent = text;
  statusMessage.classList.remove(
    "hidden",
    "status-message--error",
    "status-message--success"
  );
  statusMessage.classList.add(
    isError ? "status-message--error" : "status-message--success"
  );
}

/**
 * Hide the status message.
 */
function hideStatusMessage() {
  if (!statusMessage) return;
  statusMessage.classList.add("hidden");
  statusMessage.classList.remove("status-message--error", "status-message--success");
  statusMessage.textContent = "";
}

/**
 * Show or hide the loading spinner.
 */
function setLoading(visible) {
  if (!loadingSpinner) return;
  if (visible) {
    loadingSpinner.classList.remove("hidden");
  } else {
    loadingSpinner.classList.add("hidden");
  }
}

/**
 * Validate that a URL string starts with http:// or https:// and is well-formed.
 * Returns an error string if invalid, or null if valid.
 */
function validateApiUrl(url) {
  if (!url) {
    return "API URL is required.";
  }
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    return "API URL must start with http:// or https://";
  }
  try {
    new URL(url);
  } catch {
    return "API URL is not a valid URL.";
  }
  return null;
}

/**
 * Ping the API health endpoint to test the connection.
 * Returns { success: true } or { success: false, error: string }.
 */
async function testConnection(apiUrl, apiToken) {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(`${apiUrl}/api/v1/health`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${apiToken}`,
        Accept: "application/json",
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.status === 401 || response.status === 403) {
      return {
        success: false,
        error: "Authentication failed. Please check your API token.",
      };
    }

    if (!response.ok) {
      return {
        success: false,
        error: `Server returned ${response.status} ${response.statusText}. Check the API URL.`,
      };
    }

    return { success: true };
  } catch (err) {
    if (err.name === "AbortError") {
      return {
        success: false,
        error: "Connection timed out. The server did not respond within 10 seconds.",
      };
    }
    if (err.message?.includes("Failed to fetch") || err.message?.includes("NetworkError")) {
      return {
        success: false,
        error: "Network error. Could not reach the server. Check the URL and your internet connection.",
      };
    }
    return {
      success: false,
      error: `Connection error: ${err.message}`,
    };
  }
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

  // Clear previous status messages
  hideStatusMessage();

  if (!apiUrl || !apiToken) {
    showStatusMessage("Please enter both API URL and token.", true);
    return;
  }

  // Validate API URL format (must start with http:// or https://)
  const urlError = validateApiUrl(apiUrl);
  if (urlError) {
    showStatusMessage(urlError, true);
    return;
  }

  // Validate API token length
  if (apiToken.length < 1 || apiToken.length > 500) {
    showStatusMessage("API token must be between 1 and 500 characters.", true);
    return;
  }

  btnConnect.disabled = true;
  btnConnect.textContent = "Connecting...";
  setLoading(true);

  try {
    // Test the connection by pinging the health endpoint directly
    const connectionResult = await testConnection(apiUrl, apiToken);

    if (!connectionResult.success) {
      showStatusMessage(connectionResult.error, true);
      setLoading(false);
      btnConnect.disabled = false;
      btnConnect.textContent = "Connect";
      return;
    }

    // Connection succeeded — persist credentials
    await chrome.storage.local.set({ apiUrl, apiToken });

    // Also verify via the background service worker
    const res = await sendMessage("healthCheck");
    if (res && res.success) {
      showStatusMessage("Connected successfully!", false);
      showActions();
    } else {
      showStatusMessage(
        "Direct connection succeeded but background check failed. Check your URL and token.",
        true
      );
      showLogin();
    }
  } catch (err) {
    // Classify the error for a meaningful message
    const msg = err.message || "Unknown error";
    if (msg.includes("NetworkError") || msg.includes("Failed to fetch")) {
      showStatusMessage(
        "Network error: Could not reach the server. Verify the URL and your internet connection.",
        true
      );
    } else if (msg.includes("401") || msg.includes("403") || msg.toLowerCase().includes("auth")) {
      showStatusMessage(
        "Authentication error: Your API token was rejected. Please verify it.",
        true
      );
    } else {
      showStatusMessage(`Error: ${msg}`, true);
    }
    showLogin();
  } finally {
    setLoading(false);
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
