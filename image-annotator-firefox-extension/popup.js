// Firefox WebExtension - Image Annotator
// Popup script

const DEFAULT_SETTINGS = {
  backendEndpoint: "http://localhost:8000",
  accessCode: "",
  targetLanguage: "english"
};

// DOM elements
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const backendUrlSpan = document.getElementById("backendUrl");
const targetLangSpan = document.getElementById("targetLang");
const testBtn = document.getElementById("testBtn");
const settingsBtn = document.getElementById("settingsBtn");

// Update status display
function updateStatus(connected, text) {
  statusDot.className = "status-dot " + (connected ? "connected" : "disconnected");
  statusText.textContent = text;
}

// Load and display settings
function loadSettings() {
  return browser.storage.sync.get(Object.keys(DEFAULT_SETTINGS)).then((settings) => {
    const endpoint = settings.backendEndpoint || DEFAULT_SETTINGS.backendEndpoint;
    const lang = settings.targetLanguage || DEFAULT_SETTINGS.targetLanguage;
    const authCode = settings.accessCode || DEFAULT_SETTINGS.accessCode;
    
    backendUrlSpan.textContent = endpoint.replace(/^https?:\/\//, "").substring(0, 30) + (endpoint.length > 30 ? "..." : "");
    targetLangSpan.textContent = lang.charAt(0).toUpperCase() + lang.slice(1);
    
    // Test connection on load
    testConnection(endpoint, authCode);
    
    return { endpoint, authCode, lang };
  }).catch((err) => {
    console.error("Error loading settings:", err);
    updateStatus(false, "Error loading settings");
  });
}

// Test connection to backend
async function testConnection(endpoint, authCode) {
  updateStatus(false, "Testing connection...");
  statusDot.className = "status-dot testing";
  
  try {
    const response = await fetch(`${endpoint}/translate?target_language=english`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Code": authCode || ""
      },
      body: JSON.stringify({ text: "test" })
    });
    
    if (response.status === 401 || response.status === 200) {
      updateStatus(true, "Connected");
    } else {
      updateStatus(false, `Error (${response.status})`);
    }
  } catch (err) {
    updateStatus(false, `Offline`);
  }
}

// Open options page
function openSettings() {
  browser.runtime.openOptionsPage();
}

// Event listeners
testBtn.addEventListener("click", () => {
  browser.storage.sync.get(Object.keys(DEFAULT_SETTINGS)).then((settings) => {
    const endpoint = settings.backendEndpoint || DEFAULT_SETTINGS.backendEndpoint;
    const authCode = settings.accessCode || DEFAULT_SETTINGS.accessCode;
    testConnection(endpoint, authCode);
  });
});

settingsBtn.addEventListener("click", openSettings);

// Initialize on load
document.addEventListener("DOMContentLoaded", loadSettings);