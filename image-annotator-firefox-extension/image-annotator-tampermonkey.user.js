// ==UserScript==
// @name         Image Annotator
// @namespace    https://lookingglass
// @version      1.0
// @description  Annotate images using AI - Right-click on any image to annotate it with AI-generated labels. Configurable backend endpoint and translation language.
// @author       LookingGlass
// @match        http://*/*
// @match        https://*/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_registerMenuCommand
// @grant        GM_notification
// @connect      *
// @run-at       document-end
// ==/UserScript==

(function() {
  'use strict';

  console.log("[Image Annotator] Tampermonkey script loading...");

  // Default settings
  const DEFAULT_SETTINGS = {
    backendEndpoint: "http://localhost:8000/v1",
    accessCode: "",
    targetLanguage: "english",
    autoAnnotate: false
  };

  // Load settings from storage
  function getSettings() {
    return {
      backendEndpoint: GM_getValue("backendEndpoint", DEFAULT_SETTINGS.backendEndpoint),
      accessCode: GM_getValue("accessCode", DEFAULT_SETTINGS.accessCode),
      targetLanguage: GM_getValue("targetLanguage", DEFAULT_SETTINGS.targetLanguage),
      autoAnnotate: GM_getValue("autoAnnotate", DEFAULT_SETTINGS.autoAnnotate)
    };
  }

  // Save settings to storage
  function saveSettings(settings) {
    Object.entries(settings).forEach(([key, value]) => {
      GM_setValue(key, value);
    });
  }

  // Current settings cache
  let currentSettings = getSettings();

  // State flags
  let isTranslating = false;
  let isAnnotating = false;
  let persistentNotification = null;

  // Inject styles
  const style = document.createElement("style");
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes notificationSpinner {
      to { transform: rotate(360deg); }
    }
    .image-label-notification {
      animation: slideIn 0.3s ease !important;
    }
    .image-label-notification.loading .spinner {
      animation: notificationSpinner 0.8s linear infinite !important;
    }
  `;
  document.head.appendChild(style);

  // Register menu command for settings
  GM_registerMenuCommand("⚙️ Image Annotator Settings", openSettingsDialog);

  // Settings dialog
  function openSettingsDialog() {
    const settings = getSettings();

    const endpoint = prompt("Backend Endpoint:", settings.backendEndpoint);
    if (endpoint === null) return; // Cancelled

    const accessCode = prompt("Access Code:", settings.accessCode);
    if (accessCode === null) return;

    const targetLanguage = prompt("Target Language:", settings.targetLanguage);
    if (targetLanguage === null) return;

    saveSettings({
      backendEndpoint: endpoint || DEFAULT_SETTINGS.backendEndpoint,
      accessCode: accessCode || "",
      targetLanguage: targetLanguage || "english"
    });

    currentSettings = getSettings();
    showNotification("Settings saved", 3000);
  }

  // Create custom context menu
  function createContextMenu() {
    // Remove existing if any
    const existing = document.getElementById("image-annotator-context-menu");
    if (existing) existing.remove();

    const menu = document.createElement("div");
    menu.id = "image-annotator-context-menu";
    menu.style.cssText = `
      position: fixed;
      display: none;
      background: white;
      border: 1px solid #ccc;
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.2);
      z-index: 2147483647;
      min-width: 180px;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
    `;

    menu.innerHTML = `
      <div class="context-menu-item" data-action="annotate-image" style="padding: 10px 16px; cursor: pointer; display: flex; align-items: center; gap: 10px;">
        <span>🏷️</span>
        <span>Annotate Image</span>
      </div>
      <div class="context-menu-item" data-action="translate-text" style="padding: 10px 16px; cursor: pointer; display: flex; align-items: center; gap: 10px;">
        <span>🌐</span>
        <span>Translate Text</span>
      </div>
      <hr style="margin: 4px 0; border: none; border-top: 1px solid #eee;">
      <div class="context-menu-item" data-action="settings" style="padding: 10px 16px; cursor: pointer; display: flex; align-items: center; gap: 10px;">
        <span>⚙️</span>
        <span>Settings</span>
      </div>
    `;

    document.body.appendChild(menu);

    // Handle menu clicks
    menu.querySelectorAll(".context-menu-item").forEach(item => {
      item.addEventListener("click", (e) => {
        const action = item.dataset.action;
        hideContextMenu();

        if (action === "annotate-image" && contextMenuTarget) {
          handleAnnotateImage(contextMenuTarget.src, contextMenuTarget);
        } else if (action === "translate-text") {
          handleTranslateText();
        } else if (action === "settings") {
          openSettingsDialog();
        }
      });

      item.addEventListener("mouseenter", () => {
        item.style.background = "#f0f0f0";
      });

      item.addEventListener("mouseleave", () => {
        item.style.background = "transparent";
      });
    });

    return menu;
  }

  let contextMenuTarget = null;
  let contextMenu = null;

  // Show context menu on right-click
  document.addEventListener("contextmenu", (e) => {
    // Check if right-clicked on image
    if (e.target.tagName === "IMG") {
      e.preventDefault();
      contextMenuTarget = e.target;

      if (!contextMenu) {
        contextMenu = createContextMenu();
      }

      // Position menu
      let x = e.clientX;
      let y = e.clientY;

      // Ensure menu fits on screen
      const menuWidth = 180;
      const menuHeight = 150;

      if (x + menuWidth > window.innerWidth) {
        x = window.innerWidth - menuWidth - 10;
      }
      if (y + menuHeight > window.innerHeight) {
        y = window.innerHeight - menuHeight - 10;
      }

      contextMenu.style.left = x + "px";
      contextMenu.style.top = y + "px";
      contextMenu.style.display = "block";

      // Hide menu on click elsewhere
      const hideOnNextClick = (ev) => {
        hideContextMenu();
        document.removeEventListener("click", hideOnNextClick);
      };
      setTimeout(() => {
        document.addEventListener("click", hideOnNextClick);
      }, 100);
    }
  });

  function hideContextMenu() {
    if (contextMenu) {
      contextMenu.style.display = "none";
    }
  }

  // Handle annotation request
  function handleAnnotateImage(imageUrl, imgElement) {
    if (isAnnotating) {
      showNotification("Annotation in progress, please wait...");
      return;
    }

    isAnnotating = true;
    const dismissNotification = showPersistentNotification("Annotating image...");

    // Fetch image as blob and send to backend
    fetchImageAndAnnotate(imageUrl)
      .then((response) => {
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
      })
      .catch((err) => {
        console.error("[Image Annotator] Annotation error:", err);
        dismissNotification.dismiss();
        isAnnotating = false;
        persistentNotification = null;
        const message = err.message || "Annotation failed";
        showNotification(message);
      });
  }

  // Fetch image and annotate
  async function fetchImageAndAnnotate(imageUrl) {
    const settings = getSettings();
    const endpoint = settings.backendEndpoint || DEFAULT_SETTINGS.backendEndpoint;
    const authCode = settings.accessCode || "";
    const targetLang = settings.targetLanguage || "english";

    // Fetch image as blob using GM_xmlhttpRequest
    const blob = await fetchImageBlob(imageUrl);

    // Resize if needed
    const resizedBlob = await resizeImageBlob(blob, 1000);

    // Send to backend
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append("data", resizedBlob);

      const xhrUrl = `${endpoint}/image/annotate?translate=true&translate_language=${encodeURIComponent(targetLang)}`;

      GM_xmlhttpRequest({
        method: "POST",
        url: xhrUrl,
        headers: {
          "X-Auth-Code": authCode
        },
        data: formData,
        timeout: 600000, // 10 minutes
        onload: (response) => {
          if (response.status === 401) {
            reject(new Error("Authentication failed. Please check your access code in settings."));
            return;
          }

          if (response.status >= 400) {
            reject(new Error(`Annotation failed (${response.status})`));
            return;
          }

          try {
            const data = JSON.parse(response.responseText);
            resolve({ success: true, labels: data.labels || [] });
          } catch (err) {
            reject(new Error("Invalid response from server"));
          }
        },
        onerror: (err) => {
          reject(new Error(`Network error: ${err.error || "Unknown error"}`));
        },
        ontimeout: () => {
          reject(new Error("Annotation request timed out after 10 minutes"));
        }
      });
    });
  }

  // Fetch image as blob
  function fetchImageBlob(imageUrl) {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method: "GET",
        url: imageUrl,
        responseType: "blob",
        timeout: 60000,
        onload: (response) => {
          if (response.status >= 400) {
            reject(new Error(`Failed to fetch image (${response.status})`));
            return;
          }
          resolve(response.response);
        },
        onerror: (err) => {
          reject(new Error(`Image fetch error: ${err.error || "Unknown error"}`));
        },
        ontimeout: () => {
          reject(new Error("Image fetch timed out"));
        }
      });
    });
  }

  // Resize image blob
  async function resizeImageBlob(blob, maxDim) {
    const img = await createImageBitmap(blob);
    const width = img.width;
    const height = img.height;

    if (width <= maxDim && height <= maxDim) {
      return blob;
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
  }

  // Display labels on image
  function displayLabelsOnImage(labels, imgElement) {
    removeExistingOverlay();

    const container = findPositionedContainer(imgElement);
    if (!container) {
      console.error("[Image Annotator] Could not find positioned container for image");
      return;
    }

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

      if (label.text) {
        const textSpan = document.createElement("span");
        textSpan.textContent = label.text;
        textSpan.className = "image-label-text";
        textSpan.dataset.fullText = label.text;
        textSpan.style.cssText = `
          padding: 2px 4px;
          background: rgba(255, 255, 255, 0);
          border-radius: 2px;
          font-size: 12px;
          max-width: 100%;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          transition: background 0.2s ease, color 0.2s ease;
          color: #fff;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
          font-weight: 500;
        `;

        const tooltip = document.createElement("div");
        tooltip.className = "image-label-tooltip";
        tooltip.textContent = label.text.replace(/\n/g, " ");
        const labelWidth = (label.x2 - label.x1) * imgRect.width;
        const labelHeight = (label.y2 - label.y1) * imgRect.height;
        tooltip.style.cssText = `
          position: absolute;
          background: rgba(255, 255, 255, 0.98);
          color: #333;
          padding: 6px 10px;
          border-radius: 4px;
          font-size: 12px;
          white-space: pre-wrap;
          word-break: break-word;
          max-width: ${Math.max(labelWidth, 200)}px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
          pointer-events: none;
          z-index: 2147483647;
          display: none;
          left: ${label.x1 * imgRect.width + (labelWidth / 2)}px;
          top: ${label.y1 * imgRect.height + (labelHeight / 2)}px;
          transform: translate(-50%, -50%);
          min-width: ${labelWidth}px;
          text-align: center;
        `;

        labelDiv.addEventListener("mouseenter", (e) => {
          e.stopPropagation();
          const labelRect = labelDiv.getBoundingClientRect();
          const containerRect = overlay.getBoundingClientRect();
          const relativeLeft = labelRect.left - containerRect.left + (labelRect.width / 2);
          const relativeTop = labelRect.top - containerRect.top + (labelRect.height / 2);
          tooltip.style.left = `${relativeLeft}px`;
          tooltip.style.top = `${relativeTop}px`;
          tooltip.style.display = "block";
        });

        labelDiv.addEventListener("mouseleave", (e) => {
          e.stopPropagation();
          tooltip.style.display = "none";
        });

        labelDiv.appendChild(textSpan);
        overlay.appendChild(tooltip);
      }

      labelDiv.addEventListener("click", () => {
        overlay.remove();
      });

      overlay.appendChild(labelDiv);
    });

    container.style.position = container.style.position || "relative";
    container.appendChild(overlay);
  }

  // Find positioned container
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

  // Remove existing overlay
  function removeExistingOverlay() {
    const existing = document.querySelector(".image-label-container");
    if (existing) {
      existing.remove();
    }
  }

  // Handle translate text
  function handleTranslateText() {
    const selection = window.getSelection();
    const selectedText = selection.toString().trim();

    if (!selectedText) {
      showNotification("No text selected");
      return;
    }

    if (isTranslating) {
      showNotification("Translation in progress, please wait...");
      return;
    }

    isTranslating = true;
    const dismissNotification = showPersistentNotification("Translating...");

    translateText(selectedText)
      .then((response) => {
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
      })
      .catch((err) => {
        dismissNotification.dismiss();
        isTranslating = false;
        persistentNotification = null;
        showNotification(err.message || "Translation failed");
      });
  }

  // Translate text via API
  function translateText(text) {
    const settings = getSettings();
    const endpoint = settings.backendEndpoint || DEFAULT_SETTINGS.backendEndpoint;
    const authCode = settings.accessCode || "";
    const targetLang = settings.targetLanguage || "english";

    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method: "POST",
        url: `${endpoint}/translate?target_language=${encodeURIComponent(targetLang)}`,
        headers: {
          "Content-Type": "application/json",
          "X-Auth-Code": authCode
        },
        data: JSON.stringify({ text: text }),
        timeout: 300000, // 5 minutes
        onload: (response) => {
          if (response.status === 401) {
            resolve({ success: false, error: "Authentication failed. Please check your access code in settings." });
            return;
          }

          if (response.status >= 400) {
            resolve({ success: false, error: `Translation failed (${response.status})` });
            return;
          }

          try {
            const data = JSON.parse(response.responseText);
            resolve({ success: true, translatedText: data.translated_text || data.translation });
          } catch (err) {
            reject(new Error("Invalid response from server"));
          }
        },
        onerror: (err) => {
          reject(new Error(`Network error: ${err.error || "Unknown error"}`));
        },
        ontimeout: () => {
          reject(new Error("Translation request timed out after 5 minutes"));
        }
      });
    });
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
      spinner.className = "spinner";
      spinner.style.cssText = `
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255,255,255,0.3);
        border-top-color: white;
        border-radius: 50%;
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

  // Show persistent notification
  function showPersistentNotification(message) {
    if (persistentNotification) {
      persistentNotification.dismiss();
    }
    persistentNotification = showNotification(message, 0, true);
    return persistentNotification;
  }

  console.log("[Image Annotator] Tampermonkey script initialized");
})();
