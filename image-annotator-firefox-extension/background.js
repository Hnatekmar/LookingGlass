// Firefox WebExtension - Image Annotator
// Background script (persistent page for Firefox MV3)

console.log("[Image Annotator] Background script loading...");

// Default settings
const DEFAULT_SETTINGS = {
  backendEndpoint: "http://localhost:8000/v1",
  accessCode: "",
  targetLanguage: "english",
  autoAnnotate: false
};

// Initialize context menus on install
browser.runtime.onInstalled.addListener(() => {
  console.log("[Image Annotator] Extension installed/updated");

  // Set default settings if not already set
  browser.storage.sync.get(Object.keys(DEFAULT_SETTINGS)).then((settings) => {
    const updates = {};
    for (const [key, defaultValue] of Object.entries(DEFAULT_SETTINGS)) {
      if (settings[key] === undefined) {
        updates[key] = defaultValue;
      }
    }
    if (Object.keys(updates).length > 0) {
      browser.storage.sync.set(updates);
      console.log("[Image Annotator] Default settings initialized", updates);
    }
  }).catch((err) => {
    console.error("[Image Annotator] Error initializing settings:", err);
  });

  // Create context menus
  createContextMenus();
});

// Create context menu items
function createContextMenus() {
  // Remove existing menus first
  browser.contextMenus.removeAll().then(() => {
    // Menu for annotating images
    browser.contextMenus.create({
      id: "annotate-image",
      title: "Annotate Image",
      contexts: ["image"]
    });

    // Menu for translating selected text
    browser.contextMenus.create({
      id: "translate-text",
      title: "Translate Text",
      contexts: ["selection"]
    });

    console.log("[Image Annotator] Context menus created");
  }).catch((err) => {
    console.error("[Image Annotator] Error creating context menus:", err);
  });
}

// Handle context menu clicks
browser.contextMenus.onClicked.addListener((info, tab) => {
  console.log("[Image Annotator] Context menu clicked:", info.menuItemId, info);

  if (info.menuItemId === "annotate-image") {
    // Get the image URL
    const imageUrl = info.srcUrl;
    console.log("[Image Annotator] Annotating image:", imageUrl);

    // Send message to content script in the specific frame where image was clicked
    browser.tabs.sendMessage(tab.id, {
      action: "annotate-image",
      imageUrl: imageUrl
    }, {
      frameId: info.frameId || 0
    }).catch((err) => {
      console.error("[Image Annotator] Failed to send message:", err);
      
      // Fallback: try all frames
      console.log("[Image Annotator] Trying to send to all frames...");
      browser.tabs.sendMessage(tab.id, {
        action: "annotate-image",
        imageUrl: imageUrl
      }).catch((err2) => {
        console.error("[Image Annotator] Fallback also failed:", err2);
      });
    });
  }

  if (info.menuItemId === "translate-text") {
    // Send message to content script to translate
    browser.tabs.sendMessage(tab.id, {
      action: "translate-text"
    }).catch((err) => {
      console.error("[Image Annotator] Failed to send message:", err);
    });
  }
});

// Message handler for content script communication
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log("[Image Annotator] Message received:", message.action);

  if (message.action === "get-settings") {
    browser.storage.sync.get(Object.keys(DEFAULT_SETTINGS)).then((settings) => {
      sendResponse({ success: true, settings: settings });
    }).catch((err) => {
      console.error("[Image Annotator] Error getting settings:", err);
      sendResponse({ success: false, error: err.message });
    });
    return true; // Keep channel open for async response
  }

  if (message.action === "translate-text") {
    handleTranslateText(message.text, message.settings).then((result) => {
      sendResponse(result);
    }).catch((err) => {
      console.error("[Image Annotator] Translation error:", err);
      sendResponse({ success: false, error: err.message });
    });
    return true;
  }

  if (message.action === "annotate-image") {
    handleAnnotateImage(message.imageUrl).then((result) => {
      sendResponse(result);
    }).catch((err) => {
      console.error("[Image Annotator] Annotation error:", err);
      sendResponse({ success: false, error: err.message });
    });
    return true;
  }

  if (message.action === "fetch-image-blob") {
    handleFetchImageBlob(message.imageUrl).then((result) => {
      sendResponse(result);
    }).catch((err) => {
      console.error("[Image Annotator] Image fetch error:", err);
      sendResponse({ success: false, error: err.message });
    });
    return true;
  }

  return false;
});

// Handle text translation
async function handleTranslateText(text, settings) {
  const endpoint = settings.backendEndpoint || DEFAULT_SETTINGS.backendEndpoint;
  const authCode = settings.accessCode || "";
  const targetLang = settings.targetLanguage || "english";

  // Timeout for translation requests (5 minutes)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 600 * 1000);

  try {
    const response = await fetch(`${endpoint}/translate?target_language=${encodeURIComponent(targetLang)}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Code": authCode
      },
      body: JSON.stringify({ text: text }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.status === 401) {
      return { success: false, error: "Authentication failed. Please check your access code in settings." };
    }

    if (!response.ok) {
      return { success: false, error: `Translation failed (${response.status})` };
    }

    const data = await response.json();
    return { success: true, translatedText: data.translated_text || data.translation };
  } catch (err) {
    if (err.name === "AbortError") {
      return { success: false, error: "Translation request timed out after 30 seconds" };
    }
    return { success: false, error: `Network error: ${err.message}` };
  }
}

// Handle image blob fetch (for CORS proxying when canvas is tainted)
async function handleFetchImageBlob(imageUrl) {
  try {
    const response = await fetch(imageUrl, {
      mode: "cors",
      credentials: "omit"
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch image (${response.status})`);
    }

    const blob = await response.blob();
    const reader = new FileReader();
    
    return new Promise((resolve, reject) => {
      reader.onloadend = () => {
        const base64Data = reader.result.split(",")[1];
        resolve({
          success: true,
          base64Data: base64Data,
          mimeType: blob.type || "image/png"
        });
      };
      reader.onerror = () => reject(new Error("Failed to read blob"));
      reader.readAsDataURL(blob);
    });
  } catch (err) {
    return { success: false, error: `Image fetch error: ${err.message}` };
  }
}

// Handle image annotation (background script bypasses CSP)
async function handleAnnotateImage(imageUrl) {
  const settings = await browser.storage.sync.get(Object.keys(DEFAULT_SETTINGS));
  const endpoint = settings.backendEndpoint || DEFAULT_SETTINGS.backendEndpoint;
  const authCode = settings.accessCode || "";
  const targetLang = settings.targetLanguage || "english";

  // Fetch image as blob
  const imageResult = await handleFetchImageBlob(imageUrl);
  if (!imageResult.success) {
    throw new Error(imageResult.error);
  }

  // Convert base64 to blob
  const byteCharacters = atob(imageResult.base64Data);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  const blob = new Blob([byteArray], { type: imageResult.mimeType });

  // Resize if needed
  const resizedBlob = await resizeImageBlob(blob, 1000);

  // Send to backend
  const formData = new FormData();
  formData.append("data", resizedBlob);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 600 * 1000);

  try {
    const response = await fetch(`${endpoint}/image/annotate?translate=true&translate_language=${encodeURIComponent(targetLang)}`, {
      method: "POST",
      headers: {
        "X-Auth-Code": authCode
      },
      body: formData,
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.status === 401) {
      throw new Error("Authentication failed. Please check your access code in settings.");
    }

    if (!response.ok) {
      throw new Error(`Annotation failed (${response.status})`);
    }

    const data = await response.json();
    return { success: true, labels: data.labels || [] };
  } catch (err) {
    if (err.name === "AbortError") {
      throw new Error("Annotation request timed out after 10 minutes");
    }
    throw err;
  }
}

// Resize image blob to max dimension
async function resizeImageBlob(blob, maxDim) {
  return createImageBitmap(blob).then((img) => {
    const width = img.width;
    const height = img.height;

    if (width <= maxDim && height <= maxDim) {
      return blob; // No resize needed
    }

    let newWidth, newHeight;
    if (width > height) {
      newHeight = (height / width) * maxDim;
      newWidth = maxDim;
    } else {
      newWidth = (width / height) * maxDim;
      newHeight = maxDim;
    }

    const canvas = document.createElement("canvas");
    canvas.width = newWidth;
    canvas.height = newHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0, newWidth, newHeight);

    return new Promise((resolve) => {
      canvas.toBlob((resizedBlob) => {
        resolve(resizedBlob || blob);
      }, "image/png");
    });
  });
}

console.log("[Image Annotator] Background script initialized");
