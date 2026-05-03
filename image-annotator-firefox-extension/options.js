// Firefox WebExtension - Image Annotator
// Options page script

const DEFAULT_SETTINGS = {
  backendEndpoint: "http://localhost:8000/v1",
  accessCode: "",
  targetLanguage: "english",
  autoAnnotate: false
};

// All supported languages with flags, grouped by region.
// Codes must match SUPPORTED_LANGUAGES in app/v1/__init__.py.
const LANGUAGES = [
  // Europe
  { code: "english",    name: "English",                flag: "🇬🇧", category: "Europe" },
  { code: "french",     name: "French",                 flag: "🇫🇷", category: "Europe" },
  { code: "german",     name: "German",                 flag: "🇩🇪", category: "Europe" },
  { code: "italian",    name: "Italian",                flag: "🇮🇹", category: "Europe" },
  { code: "portuguese", name: "Portuguese",             flag: "🇵🇹", category: "Europe" },
  { code: "spanish",    name: "Spanish",                flag: "🇪🇸", category: "Europe" },
  { code: "dutch",      name: "Dutch",                  flag: "🇳🇱", category: "Europe" },
  { code: "polish",     name: "Polish",                 flag: "🇵🇱", category: "Europe" },
  { code: "russian",    name: "Russian",                flag: "🇷🇺", category: "Europe" },
  { code: "ukrainian",  name: "Ukrainian",              flag: "🇺🇦", category: "Europe" },
  { code: "turkish",    name: "Turkish",                flag: "🇹🇷", category: "Europe" },
  { code: "greek",      name: "Greek",                  flag: "🇬🇷", category: "Europe" },
  { code: "czech",      name: "Czech",                  flag: "🇨🇿", category: "Europe" },
  { code: "hungarian",  name: "Hungarian",              flag: "🇭🇺", category: "Europe" },
  { code: "romanian",   name: "Romanian",               flag: "🇷🇴", category: "Europe" },
  { code: "swedish",    name: "Swedish",                flag: "🇸🇪", category: "Europe" },
  { code: "norwegian",  name: "Norwegian",              flag: "🇳🇴", category: "Europe" },
  { code: "danish",     name: "Danish",                  flag: "🇩🇰", category: "Europe" },
  { code: "finnish",    name: "Finnish",                 flag: "🇫🇮", category: "Europe" },
  { code: "bulgarian",  name: "Bulgarian",               flag: "🇧🇬", category: "Europe" },
  { code: "croatian",   name: "Croatian",                flag: "🇭🇷", category: "Europe" },
  { code: "slovak",     name: "Slovak",                  flag: "🇸🇰", category: "Europe" },
  { code: "slovenian",  name: "Slovenian",               flag: "🇸🇮", category: "Europe" },
  { code: "lithuanian", name: "Lithuanian",              flag: "🇱🇹", category: "Europe" },
  { code: "latvian",    name: "Latvian",                 flag: "🇱🇻", category: "Europe" },
  { code: "estonian",   name: "Estonian",                flag: "🇪🇪", category: "Europe" },
  // Asia
  { code: "japanese",   name: "Japanese",               flag: "🇯🇵", category: "Asia" },
  { code: "korean",     name: "Korean",                  flag: "🇰🇷", category: "Asia" },
  { code: "chinese",    name: "Chinese (Simplified)",    flag: "🇨🇳", category: "Asia" },
  { code: "thai",       name: "Thai",                    flag: "🇹🇭", category: "Asia" },
  { code: "vietnamese", name: "Vietnamese",              flag: "🇻🇳", category: "Asia" },
  { code: "indonesian", name: "Indonesian",              flag: "🇮🇩", category: "Asia" },
  { code: "malay",      name: "Malay",                   flag: "🇲🇾", category: "Asia" },
  { code: "tamil",      name: "Tamil",                    flag: "🇮🇳", category: "Asia" },
  { code: "hindi",      name: "Hindi",                    flag: "🇮🇳", category: "Asia" },
  { code: "bengali",    name: "Bengali",                  flag: "🇧🇩", category: "Asia" },
  { code: "telugu",     name: "Telugu",                  flag: "🇮🇳", category: "Asia" },
  { code: "marathi",    name: "Marathi",                  flag: "🇮🇳", category: "Asia" },
  { code: "urdu",       name: "Urdu",                     flag: "🇵🇰", category: "Asia" },
  { code: "arabic",     name: "Arabic",                   flag: "🇸🇦", category: "Asia" },
  { code: "persian",    name: "Persian (Farsi)",          flag: "🇮🇷", category: "Asia" },
  { code: "hebrew",     name: "Hebrew",                   flag: "🇮🇱", category: "Asia" },
  { code: "burmese",    name: "Burmese",                  flag: "🇲🇲", category: "Asia" },
  { code: "khmer",      name: "Khmer",                    flag: "🇰🇭", category: "Asia" },
  { code: "lao",        name: "Lao",                       flag: "🇱🇦", category: "Asia" },
  // Africa
  { code: "swahili",    name: "Swahili",                  flag: "🇰🇪", category: "Africa" },
  { code: "afrikaans",  name: "Afrikaans",                flag: "🇿🇦", category: "Africa" },
  { code: "amharic",    name: "Amharic",                  flag: "🇪🇹", category: "Africa" },
  { code: "yoruba",     name: "Yoruba",                   flag: "🇳🇬", category: "Africa" },
  { code: "zulu",       name: "Zulu",                     flag: "🇿🇦", category: "Africa" },
  // Special
  { code: "none",       name: "None (No Translation)",     flag: "🚫", category: "Special" },
];

// State
let currentLang = "english";
let highlightedIndex = -1;
let displayedLangs = [];

// DOM elements
const backendEndpointInput = document.getElementById("backendEndpoint");
const accessCodeInput = document.getElementById("accessCode");
const autoAnnotateCheckbox = document.getElementById("autoAnnotate");
const saveBtn = document.getElementById("saveBtn");
const testBtn = document.getElementById("testBtn");
const resetBtn = document.getElementById("resetBtn");
const statusMessage = document.getElementById("statusMessage");

// Language selector elements
const langSelected = document.getElementById("langSelected");
const langSelectedFlag = document.getElementById("langSelectedFlag");
const langSelectedName = document.getElementById("langSelectedName");
const langDropdown = document.getElementById("langDropdown");
const langSearch = document.getElementById("langSearch");
const langList = document.getElementById("langList");

// Show status message
function showStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.className = isError ? "status error" : "status success";

  setTimeout(() => {
    statusMessage.className = "status";
  }, 5000);
}

// Load settings from storage
function loadSettings() {
  browser.storage.sync.get(Object.keys(DEFAULT_SETTINGS)).then((settings) => {
    backendEndpointInput.value = settings.backendEndpoint || DEFAULT_SETTINGS.backendEndpoint;
    accessCodeInput.value = settings.accessCode || DEFAULT_SETTINGS.accessCode;
    autoAnnotateCheckbox.checked = settings.autoAnnotate || DEFAULT_SETTINGS.autoAnnotate;
    
    currentLang = settings.targetLanguage || DEFAULT_SETTINGS.targetLanguage;
    updateSelectedDisplay();
  }).catch((err) => {
    console.error("Error loading settings:", err);
  });
}

// Update the selected display
function updateSelectedDisplay() {
  const lang = LANGUAGES.find(l => l.code === currentLang) || LANGUAGES[0];
  langSelectedFlag.textContent = lang.flag;
  langSelectedName.textContent = lang.name;
}

// Save settings to storage
function saveSettings() {
  const settings = {
    backendEndpoint: backendEndpointInput.value.trim(),
    accessCode: accessCodeInput.value,
    targetLanguage: currentLang,
    autoAnnotate: autoAnnotateCheckbox.checked
  };

  browser.storage.sync.set(settings).then(() => {
    showStatus("Settings saved successfully!");

    // Notify all tabs of settings update
    browser.tabs.query({}).then((tabs) => {
      tabs.forEach((tab) => {
        browser.tabs.sendMessage(tab.id, {
          action: "settings-updated",
          settings: settings
        }).catch(() => {
          // Tab might not have content script loaded
        });
      });
    });
  }).catch((err) => {
    showStatus("Failed to save settings: " + err.message, true);
  });
}

// Reset settings to defaults
function resetSettings() {
  browser.storage.sync.set(DEFAULT_SETTINGS).then(() => {
    loadSettings();
    showStatus("Settings reset to defaults");
  }).catch((err) => {
    showStatus("Failed to reset settings: " + err.message, true);
  });
}

// Test connection to backend
async function testConnection() {
  const endpoint = backendEndpointInput.value.trim() || DEFAULT_SETTINGS.backendEndpoint;
  const authCode = accessCodeInput.value;

  showStatus("Testing connection...");

  try {
    const response = await fetch(`${endpoint}/translate?target_language=english`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Code": authCode
      },
      body: JSON.stringify({ text: "test" })
    });

    if (response.status === 401 || response.status === 200) {
      showStatus(`Backend reachable at ${endpoint}`);
    } else {
      showStatus(`Backend returned status ${response.status}`, true);
    }
  } catch (err) {
    showStatus(`Connection failed: ${err.message}`, true);
  }
}

// Language dropdown logic
function openDropdown() {
  langSelected.classList.add("open");
  langDropdown.classList.add("open");
  langSearch.value = "";
  highlightedIndex = -1;
  renderLangList(LANGUAGES);
  langSearch.focus();
}

function closeDropdown() {
  langSelected.classList.remove("open");
  langDropdown.classList.remove("open");
  langSearch.value = "";
}

function toggleDropdown() {
  if (langDropdown.classList.contains("open")) {
    closeDropdown();
  } else {
    openDropdown();
  }
}

function selectLang(code) {
  currentLang = code;
  updateSelectedDisplay();
  closeDropdown();
}

function renderLangList(langs) {
  langList.innerHTML = "";
  displayedLangs = langs;

  if (langs.length === 0) {
    langList.innerHTML = '<div class="lang-empty">No languages found</div>';
    return;
  }

  let currentCategory = null;
  langs.forEach((lang, index) => {
    // Add category header if new category
    if (lang.category !== currentCategory) {
      currentCategory = lang.category;
      const catEl = document.createElement("div");
      catEl.className = "lang-category";
      catEl.textContent = currentCategory;
      langList.appendChild(catEl);
    }

    const el = document.createElement("div");
    el.className = "lang-option" + (lang.code === currentLang ? " selected" : "");
    el.dataset.index = index;
    el.innerHTML = `
      <span class="lang-option-flag">${lang.flag}</span>
      <span class="lang-option-name">${lang.name}</span>
      <span class="lang-option-code">${lang.code}</span>
    `;
    el.addEventListener("click", () => selectLang(lang.code));
    langList.appendChild(el);
  });
}

function filterLangs(query) {
  const q = query.toLowerCase().trim();
  const filtered = LANGUAGES.filter(lang =>
    lang.name.toLowerCase().includes(q) ||
    lang.code.toLowerCase().includes(q) ||
    lang.category.toLowerCase().includes(q)
  );
  highlightedIndex = -1;
  renderLangList(filtered);
}

function highlightNext() {
  const items = langList.querySelectorAll(".lang-option");
  if (items.length === 0) return;
  
  if (highlightedIndex >= 0) {
    items[highlightedIndex].classList.remove("highlighted");
  }
  
  highlightedIndex = (highlightedIndex + 1) % items.length;
  items[highlightedIndex].classList.add("highlighted");
  items[highlightedIndex].scrollIntoView({ block: "nearest" });
}

function highlightPrev() {
  const items = langList.querySelectorAll(".lang-option");
  if (items.length === 0) return;
  
  if (highlightedIndex <= 0) {
    highlightedIndex = items.length - 1;
  } else {
    highlightedIndex--;
  }
  
  items.forEach(i => i.classList.remove("highlighted"));
  items[highlightedIndex].classList.add("highlighted");
  items[highlightedIndex].scrollIntoView({ block: "nearest" });
}

function confirmHighlighted() {
  if (highlightedIndex >= 0 && displayedLangs[highlightedIndex]) {
    selectLang(displayedLangs[highlightedIndex].code);
  }
}

// Event listeners
saveBtn.addEventListener("click", saveSettings);
resetBtn.addEventListener("click", resetSettings);
testBtn.addEventListener("click", testConnection);

langSelected.addEventListener("click", toggleDropdown);

// Close dropdown when clicking outside
document.addEventListener("click", (e) => {
  const selector = document.getElementById("langSelector");
  if (!selector.contains(e.target)) {
    closeDropdown();
  }
});

// Search input
langSearch.addEventListener("input", (e) => {
  filterLangs(e.target.value);
});

// Keyboard navigation
langSearch.addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown") {
    e.preventDefault();
    highlightNext();
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    highlightPrev();
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (highlightedIndex >= 0) {
      confirmHighlighted();
    } else {
      // Auto-select first match if searching
      const items = langList.querySelectorAll(".lang-option");
      if (items.length === 1) {
        const idx = parseInt(items[0].dataset.index);
        selectLang(displayedLangs[idx].code);
      }
    }
  } else if (e.key === "Escape") {
    closeDropdown();
  }
});

// Load settings on page load
document.addEventListener("DOMContentLoaded", loadSettings);