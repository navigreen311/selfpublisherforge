/**
 * service-worker.js — Background service worker (Manifest V3).
 *
 * Handles API communication, auth-token management, and data sync
 * between the extension and the SelfPublisherForge backend.
 */

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const API_V1 = "/api/v1";

// ---------------------------------------------------------------------------
// Storage helpers
// ---------------------------------------------------------------------------

async function getAuth() {
  const { apiUrl, apiToken } = await chrome.storage.local.get([
    "apiUrl",
    "apiToken",
  ]);
  return { apiUrl, apiToken };
}

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

async function apiRequest(method, path, body = null) {
  const { apiUrl, apiToken } = await getAuth();
  if (!apiUrl || !apiToken) {
    return { success: false, error: "Not authenticated" };
  }

  const url = `${apiUrl}${API_V1}${path}`;
  const headers = {
    Authorization: `Bearer ${apiToken}`,
    "Content-Type": "application/json",
  };

  try {
    const options = { method, headers };
    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    if (!response.ok) {
      const errorText = await response.text();
      return {
        success: false,
        error: `HTTP ${response.status}: ${errorText}`,
        status: response.status,
      };
    }

    const data = await response.json();
    return { success: true, data: data.data || data };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------

async function healthCheck() {
  const { apiUrl } = await getAuth();
  if (!apiUrl) return { success: false, error: "No API URL configured" };

  try {
    const response = await fetch(`${apiUrl}/health`);
    if (response.ok) {
      return { success: true };
    }
    return { success: false, error: `HTTP ${response.status}` };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// ---------------------------------------------------------------------------
// Save extracted Amazon data
// ---------------------------------------------------------------------------

async function saveExtraction(data) {
  return apiRequest("POST", "/extension/extract", { data });
}

// ---------------------------------------------------------------------------
// Quick research
// ---------------------------------------------------------------------------

async function quickResearch(asin) {
  const params = new URLSearchParams();
  if (asin) params.set("asin", asin);
  const query = params.toString();
  return apiRequest("GET", `/extension/quick-research${query ? "?" + query : ""}`);
}

// ---------------------------------------------------------------------------
// Save clip to Knowledge Vault
// ---------------------------------------------------------------------------

async function saveClip(clip) {
  return apiRequest("POST", "/extension/clip", clip);
}

// ---------------------------------------------------------------------------
// Message handler
// ---------------------------------------------------------------------------

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const { action } = message;

  const handlers = {
    healthCheck: () => healthCheck(),
    saveExtraction: () => saveExtraction(message.data),
    quickResearch: () => quickResearch(message.asin),
    saveClip: () => saveClip(message.clip),
    pageDetected: () => {
      // Update badge to indicate an Amazon product was detected
      if (sender.tab && sender.tab.id) {
        chrome.action.setBadgeText({ text: "!", tabId: sender.tab.id });
        chrome.action.setBadgeBackgroundColor({
          color: "#4CAF50",
          tabId: sender.tab.id,
        });
      }
      return Promise.resolve({ success: true });
    },
  };

  const handler = handlers[action];
  if (handler) {
    handler()
      .then((result) => sendResponse(result))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true; // keep the message channel open for async
  }

  sendResponse({ success: false, error: `Unknown action: ${action}` });
  return false;
});

// ---------------------------------------------------------------------------
// Extension install / update
// ---------------------------------------------------------------------------

chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === "install") {
    console.log("SelfPublisherForge extension installed.");
  } else if (details.reason === "update") {
    console.log(`SelfPublisherForge extension updated to v${chrome.runtime.getManifest().version}`);
  }
});
