// Firefox WebExtension - Image Annotator
// Content script - handles image annotation overlay

console.log("[Image Annotator] Content script loaded");

// Inject keyframe styles for notification spinner
const style = document.createElement("style");
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  @keyframes notificationSpinner {
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(style);

// Current settings cache
let currentSettings = {
  backendEndpoint: "",
  accessCode: "",
  targetLanguage: "english"
};

let isTranslating = false;
let isAnnotating = false;
let persistentNotification = null;

// Load settings from background
function loadSettings() {
  return browser.runtime.sendMessage({ action: "get-settings" }).then((response) => {
    if (response.success) {
      currentSettings = { ...currentSettings, ...response.settings };
    }
    return response;
  });
}

// Handle annotation request
function handleAnnotateImage(imageUrl, imgElement) {
  // Prevent spam: block if already annotating
  if (isAnnotating) {
    showNotification("Annotation in progress, please wait...");
    return;
  }

  isAnnotating = true;
  const dismissNotification = showPersistentNotification("Annotating image...");

  // Send to background script to handle (bypasses CSP)
  browser.runtime.sendMessage({
    action: "annotate-image",
    imageUrl: imageUrl
  }).then((response) => {
    dismissNotification.dismiss();
    isAnnotating = false;
    persistentNotification = null;

    if (response.success) {
      if (response.labels && response.labels.length > 0) {
        displayLabelsOnImage(response.labels, imgElement);
        showNotification(`Found ${response.labels.length} text region(s)`);
      } else {
        showNotification("No text found in image");
      }
    } else {
      showNotification(response.error || "Annotation failed");
    }
  }).catch((err) => {
    console.error("[Image Annotator] Annotation error:", err);
    dismissNotification.dismiss();
    isAnnotating = false;
    persistentNotification = null;
    const message = err.name === "AbortError" ? "Annotation timed out after 10 minutes" : (err.message || "Annotation failed");
    showNotification(message);
  });
}

// Fetch image as blob by drawing existing img element to canvas
// NOTE: This is kept for potential future use, but currently background script handles fetching
function fetchImageAsBlob(imgElementOrUrl) {
  console.warn("[Image Annotator] fetchImageAsBlob is deprecated - background script now handles image fetching");
  return Promise.reject(new Error("Image fetching moved to background script"));
}

function imgElementToBlob(imgElement) {
  console.warn("[Image Annotator] imgElementToBlob is deprecated");
  return Promise.reject(new Error("Image fetching moved to background script"));
}

// Display labels on image
function displayLabelsOnImage(labels, imgElement) {
  // Remove existing overlay
  removeExistingOverlay();

  // Find the positioned container for the image
  const container = findPositionedContainer(imgElement);
  if (!container) {
    console.error("[Image Annotator] Could not find positioned container for image");
    return;
  }

  // Create overlay container
  const overlay = document.createElement("div");
  overlay.className = "image-label-container";
  overlay.style.cssText = `
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 2147483647;
  `;

  // Calculate image position relative to container
  const imgRect = imgElement.getBoundingClientRect();
  const containerRect = container.getBoundingClientRect();

  const offsetX = imgRect.left - containerRect.left;
  const offsetY = imgRect.top - containerRect.top;

  labels.forEach((label, index) => {
    const labelDiv = document.createElement("div");
    labelDiv.className = "image-label";
    labelDiv.dataset.index = index;
    labelDiv.style.cssText = `
      position: absolute;
      left: ${offsetX + label.x1 * imgRect.width}px;
      top: ${offsetY + label.y1 * imgRect.height}px;
      width: ${(label.x2 - label.x1) * imgRect.width}px;
      height: ${(label.y2 - label.y1) * imgRect.height}px;
      border: 2px solid #ff6b6b;
      background: rgba(255, 107, 107, 0.2);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      color: #333;
      text-align: center;
      overflow: hidden;
      pointer-events: auto;
      cursor: pointer;
      box-sizing: border-box;
      border-radius: 4px;
    `;

    // Add text label if provided
    if (label.text) {
      const textSpan = document.createElement("span");
      textSpan.textContent = label.text;
      textSpan.style.cssText = `
        padding: 2px 4px;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 2px;
        font-size: 12px;
        max-width: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      `;
      labelDiv.appendChild(textSpan);
    }

    // Click to remove
    labelDiv.addEventListener("click", () => {
      overlay.remove();
    });

    overlay.appendChild(labelDiv);
  });

  container.style.position = container.style.position || "relative";
  container.appendChild(overlay);
}

// Find the positioned parent container for an element
function findPositionedContainer(element) {
  let current = element.parentElement;
  while (current && current !== document.body) {
    const position = window.getComputedStyle(current).position;
    if (position === "relative" || position === "absolute" || position === "fixed") {
      return current;
    }
    current = current.parentElement;
  }
  return document.body;
}

// Remove existing label overlay
function removeExistingOverlay() {
  const existing = document.querySelector(".image-label-container");
  if (existing) {
    existing.remove();
  }
}

// Show notification
function showNotification(message, duration = 3000, loading = false) {
  const existing = document.querySelector(".image-label-notification");
  if (existing) {
    existing.remove();
  }

  const notification = document.createElement("div");
  notification.className = "image-label-notification";
  notification.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 12px 20px;
    background: #333;
    color: white;
    border-radius: 8px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    z-index: 2147483647;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    animation: slideIn 0.3s ease;
    display: flex;
    align-items: center;
    gap: 10px;
  `;

  if (loading) {
    const spinner = document.createElement("div");
    spinner.style.cssText = `
      width: 16px;
      height: 16px;
      border: 2px solid rgba(255,255,255,0.3);
      border-top-color: white;
      border-radius: 50%;
      animation: notificationSpinner 0.8s linear infinite;
    `;
    notification.appendChild(spinner);
  }

  const text = document.createElement("span");
  text.textContent = message;
  notification.appendChild(text);

  document.body.appendChild(notification);

  if (duration > 0) {
    setTimeout(() => {
      notification.style.opacity = "0";
      notification.style.transition = "opacity 0.3s ease";
      setTimeout(() => notification.remove(), 300);
    }, duration);
  }

  return {
    dismiss: () => {
      notification.style.opacity = "0";
      notification.style.transition = "opacity 0.3s ease";
      setTimeout(() => notification.remove(), 300);
    }
  };
}

// Show persistent notification that stays until explicitly dismissed
function showPersistentNotification(message) {
  if (persistentNotification) {
    persistentNotification.dismiss();
  }
  persistentNotification = showNotification(message, 0, true); // loading=true
  return persistentNotification;
}

// Handle translate text request
function handleTranslateText() {
  const selection = window.getSelection();
  const selectedText = selection.toString().trim();

  if (!selectedText) {
    showNotification("No text selected");
    return;
  }

  // Prevent spam: block if already translating
  if (isTranslating) {
    showNotification("Translation in progress, please wait...");
    return;
  }

  isTranslating = true;
  const dismissNotification = showPersistentNotification("Translating...");

  browser.runtime.sendMessage({
    action: "translate-text",
    text: selectedText,
    settings: currentSettings
  }).then((response) => {
    dismissNotification.dismiss();
    isTranslating = false;
    persistentNotification = null;

    if (response.success) {
      const range = selection.getRangeAt(0);
      range.deleteContents();
      range.insertNode(document.createTextNode(response.translatedText));
      showNotification("Translation complete");
    } else {
      showNotification(response.error || "Translation failed");
    }
  }).catch((err) => {
    dismissNotification.dismiss();
    isTranslating = false;
    persistentNotification = null;
    showNotification(err.message || "Translation failed");
  });
}

// Initialize content script
loadSettings().then(() => {
  console.log("[Image Annotator] Settings loaded", currentSettings);

  // Listen for messages from background
  browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("[Image Annotator] Content script received message:", message.action);
    
    if (message.action === "annotate-image") {
      const imageUrl = message.imageUrl;
      console.log("[Image Annotator] Searching for image:", imageUrl);
      
      if (imageUrl) {
        // Find the image element using multiple strategies
        let imgElement = null;
        
        // Strategy 1: Exact src match
        imgElement = document.querySelector(`img[src="${imageUrl}"]`);
        console.log("[Image Annotator] Strategy 1 (exact match):", imgElement ? "FOUND" : "NOT FOUND");
        
        // Strategy 2: Match by filename (last part of URL)
        if (!imgElement) {
          const filename = imageUrl.split("/").pop();
          imgElement = document.querySelector(`img[src*="${filename}"]`);
          console.log("[Image Annotator] Strategy 2 (filename:", filename, "):", imgElement ? "FOUND" : "NOT FOUND");
        }
        
        // Strategy 3: Match by URL without protocol
        if (!imgElement) {
          const urlWithoutProtocol = imageUrl.replace(/^https?:\/\//, '');
          imgElement = document.querySelector(`img[src*="${urlWithoutProtocol.split("/").slice(0, 3).join("/")}"]`);
          console.log("[Image Annotator] Strategy 3 (path match):", imgElement ? "FOUND" : "NOT FOUND");
        }
        
        // Strategy 4: Find any visible image on page (fallback)
        if (!imgElement) {
          const allImages = Array.from(document.querySelectorAll('img'));
          console.log("[Image Annotator] All images on page:", allImages.map(img => ({
            src: img.src.substring(0, 100),
            width: img.offsetWidth,
            height: img.offsetHeight,
            visible: img.offsetWidth > 0 && img.offsetHeight > 0
          })));
          
          // Extract key parts from the target URL
          const urlParts = imageUrl.split("/");
          const filename = urlParts.pop(); // c58u639kmvyg1.png?width=...
          const filenameNoParams = filename.split("?")[0]; // c58u639kmvyg1.png
          const domainAndPath = urlParts.join("/"); // https://preview.redd.it
          
          console.log("[Image Annotator] Target URL parts:", { filename, filenameNoParams, domainAndPath });
          
          // Try to find by filename without query params
          imgElement = allImages.find(img => {
            const imgSrc = img.src;
            return img.offsetWidth > 0 && img.offsetHeight > 0 && (
              imgSrc.includes(filenameNoParams) ||
              imgSrc.includes(filename.split("?")[0]) ||
              imgSrc.includes("preview.redd.it")
            );
          }) || null;
          
          console.log("[Image Annotator] Strategy 4 (search by filename/domain):", imgElement ? "FOUND: " + imgElement.src : "NOT FOUND");
        }
        
        if (imgElement) {
          console.log("[Image Annotator] Found image element:", imgElement.src);
          handleAnnotateImage(imageUrl, imgElement);
        } else {
          console.error("[Image Annotator] Could not find image element");
          showNotification("No image found");
        }
      } else {
        showNotification("No image found");
      }
    }

    if (message.action === "translate-text") {
      handleTranslateText();
    }

    if (message.action === "settings-updated") {
      currentSettings = { ...currentSettings, ...message.settings };
      showNotification("Settings updated");
    }
  });
});

console.log("[Image Annotator] Content script initialized");
