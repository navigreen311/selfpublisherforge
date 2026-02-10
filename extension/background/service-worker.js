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
const UPDATE_CHECK_ALARM = "spf-update-check";
const UPDATE_CHECK_INTERVAL_MINUTES = 360; // 6 hours

const MAX_PENDING_EXTRACTIONS = 50;
const RETRY_ALARM = "spf-retry-pending";
const RETRY_INTERVAL_MINUTES = 5;

// ---------------------------------------------------------------------------
// Retry with exponential backoff
// ---------------------------------------------------------------------------

/**
 * Wrapper around fetch() that retries on server errors (5xx) and network
 * failures with exponential backoff. Client errors (4xx) are NOT retried.
 */
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
  let lastError;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);
      if (response.ok || (response.status >= 400 && response.status < 500)) {
        return response;
      }
      // Server error — retry
      lastError = new Error(`HTTP ${response.status}`);
    } catch (err) {
      // Network failure — retry
      lastError = err;
    }
    if (attempt < maxRetries) {
      const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw lastError;
}

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

    const response = await fetchWithRetry(url, options);
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
    const response = await fetchWithRetry(`${apiUrl}/health`, {}, 2);
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
  const result = await apiRequest("POST", "/extension/extract", { data });
  if (!result.success && (!result.status || result.status >= 500)) {
    // Server error or network failure — queue for retry
    await queueExtraction(data);
  }
  return result;
}

// ---------------------------------------------------------------------------
// Offline extraction queue
// ---------------------------------------------------------------------------

async function queueExtraction(data) {
  const { pendingExtractions = [] } = await chrome.storage.local.get(["pendingExtractions"]);
  const queue = pendingExtractions.slice(-(MAX_PENDING_EXTRACTIONS - 1));
  queue.push({ data, timestamp: Date.now() });
  await chrome.storage.local.set({ pendingExtractions: queue });
  console.log(`[SPF] Extraction queued for retry. Queue size: ${queue.length}`);
}

async function retryPendingExtractions() {
  const { pendingExtractions = [] } = await chrome.storage.local.get(["pendingExtractions"]);
  if (pendingExtractions.length === 0) return;

  console.log(`[SPF] Retrying ${pendingExtractions.length} pending extraction(s)...`);
  const remaining = [];

  for (const item of pendingExtractions) {
    const result = await apiRequest("POST", "/extension/extract", { data: item.data });
    if (!result.success) {
      if (result.status && result.status >= 400 && result.status < 500) {
        // Client error — drop from queue (not retryable)
        console.warn("[SPF] Dropping non-retryable extraction:", result.error);
      } else {
        remaining.push(item);
      }
    }
  }

  await chrome.storage.local.set({ pendingExtractions: remaining });
  if (remaining.length > 0) {
    console.log(`[SPF] ${remaining.length} extraction(s) still pending.`);
  } else {
    console.log("[SPF] All pending extractions processed.");
  }
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
// Version comparison helper
// ---------------------------------------------------------------------------

/**
 * Compare two semver strings (e.g. "1.2.3" vs "1.3.0").
 * Returns  1 if a > b,  -1 if a < b,  0 if equal.
 */
function compareSemver(a, b) {
  const pa = a.split(".").map(Number);
  const pb = b.split(".").map(Number);
  for (let i = 0; i < 3; i++) {
    const diff = (pa[i] || 0) - (pb[i] || 0);
    if (diff !== 0) return diff > 0 ? 1 : -1;
  }
  return 0;
}

// ---------------------------------------------------------------------------
// Auto-update check
// ---------------------------------------------------------------------------

/**
 * Call the backend /extension/version endpoint and compare with the
 * locally-installed version. If an update is available, fire a Chrome
 * notification and store the result in chrome.storage.local.
 */
async function checkForUpdate() {
  const { apiUrl } = await chrome.storage.local.get(["apiUrl"]);
  if (!apiUrl) {
    console.log("[SPF] Skipping update check — no API URL configured.");
    return;
  }

  try {
    const response = await fetch(`${apiUrl}${API_V1}/extension/version`);
    if (!response.ok) {
      console.warn(`[SPF] Version check failed: HTTP ${response.status}`);
      return;
    }

    const json = await response.json();
    const remote = json.data || json;
    const localVersion = chrome.runtime.getManifest().version;

    // Persist timestamp regardless of result
    await chrome.storage.local.set({
      lastUpdateCheck: Date.now(),
      latestVersion: remote.version,
    });

    const updateAvailable = compareSemver(remote.version, localVersion) > 0;

    if (updateAvailable) {
      await chrome.storage.local.set({ updateAvailable: true });

      // Show a notification so the user knows an update is ready
      chrome.notifications.create("spf-update-available", {
        type: "basic",
        iconUrl: chrome.runtime.getURL("icons/icon128.png"),
        title: "SelfPublisherForge Update Available",
        message: `Version ${remote.version} is available (you have ${localVersion}). Click to update.`,
        priority: 1,
      });
    } else {
      await chrome.storage.local.set({ updateAvailable: false });
    }

    // Warn if the installed version is below the minimum supported version
    if (compareSemver(localVersion, remote.min_version) < 0) {
      chrome.notifications.create("spf-update-required", {
        type: "basic",
        iconUrl: chrome.runtime.getURL("icons/icon128.png"),
        title: "SelfPublisherForge Update Required",
        message: `Your version (${localVersion}) is below the minimum supported version (${remote.min_version}). Please update now.`,
        priority: 2,
      });
    }

    console.log(
      `[SPF] Update check complete. Local: ${localVersion}, Remote: ${remote.version}, Update available: ${updateAvailable}`
    );
  } catch (err) {
    console.warn("[SPF] Update check error:", err.message);
  }
}

// ---------------------------------------------------------------------------
// Notification click handler — open the update URL
// ---------------------------------------------------------------------------

chrome.notifications.onClicked.addListener(async (notificationId) => {
  if (
    notificationId === "spf-update-available" ||
    notificationId === "spf-update-required"
  ) {
    const { apiUrl } = await chrome.storage.local.get(["apiUrl"]);
    if (apiUrl) {
      try {
        const response = await fetch(`${apiUrl}${API_V1}/extension/version`);
        if (response.ok) {
          const json = await response.json();
          const remote = json.data || json;
          chrome.tabs.create({ url: remote.update_url });
        }
      } catch {
        // Fallback — open the self-hosted update page
        chrome.tabs.create({
          url: "https://selfpublisherforge.com/extension/updates.xml",
        });
      }
    }
    chrome.notifications.clear(notificationId);
  }
});

// ---------------------------------------------------------------------------
// Alarm handler — periodic update checks every 6 hours
// ---------------------------------------------------------------------------

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === UPDATE_CHECK_ALARM) {
    checkForUpdate();
  }
  if (alarm.name === RETRY_ALARM) {
    retryPendingExtractions();
  }
});

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
    checkForUpdate: () =>
      checkForUpdate().then(() => ({ success: true })),
    retryPending: () => retryPendingExtractions().then(() => ({ success: true })),
    getPendingCount: async () => {
      const { pendingExtractions = [] } = await chrome.storage.local.get(["pendingExtractions"]);
      return { success: true, data: { count: pendingExtractions.length } };
    },
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
    console.log(
      `SelfPublisherForge extension updated to v${chrome.runtime.getManifest().version}`
    );
    // Clear stale update flag after a successful update
    chrome.storage.local.set({ updateAvailable: false });
  }

  // Register a periodic alarm for update checks (every 6 hours).
  // The first check fires immediately via delayInMinutes: 0.1 (~6 seconds).
  chrome.alarms.create(UPDATE_CHECK_ALARM, {
    delayInMinutes: 0.1,
    periodInMinutes: UPDATE_CHECK_INTERVAL_MINUTES,
  });

  // Register a periodic alarm for retrying pending extractions
  chrome.alarms.create(RETRY_ALARM, {
    delayInMinutes: 1,
    periodInMinutes: RETRY_INTERVAL_MINUTES,
  });
});

// ---------------------------------------------------------------------------
// Also check on browser startup (service worker can restart independently)
// ---------------------------------------------------------------------------

chrome.runtime.onStartup.addListener(() => {
  // Ensure the alarm still exists (alarms can be cleared on browser restart)
  chrome.alarms.get(UPDATE_CHECK_ALARM, (alarm) => {
    if (!alarm) {
      chrome.alarms.create(UPDATE_CHECK_ALARM, {
        delayInMinutes: 1,
        periodInMinutes: UPDATE_CHECK_INTERVAL_MINUTES,
      });
    }
  });
  chrome.alarms.get(RETRY_ALARM, (alarm) => {
    if (!alarm) {
      chrome.alarms.create(RETRY_ALARM, {
        delayInMinutes: 1,
        periodInMinutes: RETRY_INTERVAL_MINUTES,
      });
    }
  });
});
