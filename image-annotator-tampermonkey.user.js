// ==UserScript==
// @name         Image Annotator
// @namespace    https://lookingglass
// @version      2.0
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

  // Inject base styles
  const style = document.createElement("style");
  style.textContent = `
    @keyframes lgSlideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes lgSlideInUp {
      from { transform: translateY(20px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
    @keyframes lgFadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    @keyframes lgSpinner {
      to { transform: rotate(360deg); }
    }
    @keyframes lgPulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    .lg-notification {
      animation: lgSlideIn 0.3s ease !important;
    }
    .lg-notification.loading .lg-spinner {
      animation: lgSpinner 0.8s linear infinite !important;
    }
    .lg-modal-overlay {
      animation: lgFadeIn 0.2s ease !important;
    }
    .lg-modal {
      animation: lgSlideInUp 0.3s ease !important;
    }
  `;
  document.head.appendChild(style);

  // Register menu command for settings
  GM_registerMenuCommand("⚙️ Image Annotator Settings", openSettingsDialog);

  // ========== MODAL COMPONENT ==========
  function createModal(title, content, actions) {
    // Remove existing modal
    removeExistingModal();

    const overlay = document.createElement("div");
    overlay.className = "lg-modal-overlay";
    overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(4px);
      z-index: 2147483646;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    `;

    const modal = document.createElement("div");
    modal.className = "lg-modal";
    modal.style.cssText = `
      background: #ffffff;
      border-radius: 16px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
      max-width: 480px;
      width: 100%;
      max-height: 90vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    `;

    // Header
    const header = document.createElement("div");
    header.style.cssText = `
      padding: 20px 24px;
      border-bottom: 1px solid #e5e7eb;
      display: flex;
      align-items: center;
      justify-content: space-between;
    `;

    const titleEl = document.createElement("h3");
    titleEl.textContent = title;
    titleEl.style.cssText = `
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 18px;
      font-weight: 600;
      color: #111827;
      margin: 0;
    `;

    const closeBtn = document.createElement("button");
    closeBtn.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    `;
    closeBtn.style.cssText = `
      background: none;
      border: none;
      cursor: pointer;
      padding: 4px;
      border-radius: 6px;
      color: #6b7280;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    `;
    closeBtn.onmouseover = () => { closeBtn.style.background = "#f3f4f6"; closeBtn.style.color = "#111827"; };
    closeBtn.onmouseout = () => { closeBtn.style.background = "none"; closeBtn.style.color = "#6b7280"; };
    closeBtn.onclick = removeExistingModal;

    header.appendChild(titleEl);
    header.appendChild(closeBtn);

    // Content
    const contentEl = document.createElement("div");
    contentEl.style.cssText = `
      padding: 24px;
      overflow-y: auto;
      flex: 1;
    `;
    contentEl.appendChild(content);

    // Actions
    const actionsEl = document.createElement("div");
    actionsEl.style.cssText = `
      padding: 16px 24px;
      border-top: 1px solid #e5e7eb;
      display: flex;
      gap: 12px;
      justify-content: flex-end;
      background: #f9fafb;
    `;

    actions.forEach(action => {
      const btn = document.createElement("button");
      btn.textContent = action.label;
      btn.className = action.primary ? "lg-btn-primary" : "lg-btn-secondary";
      btn.style.cssText = `
        padding: 10px 20px;
        border-radius: 8px;
        font-family: inherit;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        border: ${action.primary ? 'none' : '1px solid #d1d5db'};
        background: ${action.primary ? '#3b82f6' : '#ffffff'};
        color: ${action.primary ? '#ffffff' : '#374151'};
      `;

      if (action.primary) {
        btn.onmouseover = () => { btn.style.background = "#2563eb"; btn.style.transform = "translateY(-1px)"; };
        btn.onmouseout = () => { btn.style.background = "#3b82f6"; btn.style.transform = "none"; };
      } else {
        btn.onmouseover = () => { btn.style.background = "#f3f4f6"; btn.style.borderColor = "#9ca3af"; };
        btn.onmouseout = () => { btn.style.background = "#ffffff"; btn.style.borderColor = "#d1d5db"; };
      }

      btn.onclick = () => {
        if (action.onClick) action.onClick();
        removeExistingModal();
      };

      actionsEl.appendChild(btn);
    });

    modal.appendChild(header);
    modal.appendChild(contentEl);
    modal.appendChild(actionsEl);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    // Close on overlay click
    overlay.onclick = (e) => {
      if (e.target === overlay) removeExistingModal();
    };

    return { overlay, modal, content: contentEl };
  }

  function removeExistingModal() {
    const existing = document.querySelector(".lg-modal-overlay");
    if (existing) existing.remove();
  }

  // ========== SETTINGS DIALOG ==========
  function openSettingsDialog() {
    const settings = getSettings();

    const content = document.createElement("div");
    content.style.cssText = `
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;

    // Endpoint field
    const endpointGroup = createFormField("Backend Endpoint", "text", settings.backendEndpoint, "Enter your backend API endpoint", "endpoint");
    content.appendChild(endpointGroup);

    // Access Code field
    const accessCodeGroup = createFormField("Access Code", "password", settings.accessCode, "Enter your access code for authentication", "accessCode");
    content.appendChild(accessCodeGroup);

    // Target Language field
    const languageGroup = createFormField("Target Language", "text", settings.targetLanguage, "Language for translations (e.g., english, spanish)", "targetLanguage");
    content.appendChild(languageGroup);

    // Test connection button
    const testSection = document.createElement("div");
    testSection.style.cssText = `
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid #e5e7eb;
    `;

    const testBtn = document.createElement("button");
    testBtn.textContent = "Test Connection";
    testBtn.style.cssText = `
      padding: 8px 16px;
      border-radius: 6px;
      font-family: inherit;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
      border: 1px solid #d1d5db;
      background: #ffffff;
      color: #374151;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    `;
    testBtn.onmouseover = () => { testBtn.style.background = "#f3f4f6"; };
    testBtn.onmouseout = () => { testBtn.style.background = "#ffffff"; };
    testBtn.onclick = () => testConnection(testBtn);

    const testIcon = document.createElement("span");
    testIcon.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
      </svg>
    `;
    testBtn.insertBefore(testIcon, testBtn.firstChild);

    testSection.appendChild(testBtn);
    content.appendChild(testSection);

    createModal(
      "⚙️ Image Annotator Settings",
      content,
      [
        { label: "Cancel", primary: false, onClick: () => {} },
        {
          label: "Save Settings",
          primary: true,
          onClick: () => {
            const newSettings = {
              backendEndpoint: document.getElementById("endpoint").value || DEFAULT_SETTINGS.backendEndpoint,
              accessCode: document.getElementById("accessCode").value,
              targetLanguage: document.getElementById("targetLanguage").value || "english"
            };
            saveSettings(newSettings);
            currentSettings = getSettings();
            showNotification("Settings saved successfully", "success");
          }
        }
      ]
    );
  }

  function createFormField(label, type, value, placeholder, id) {
    const group = document.createElement("div");
    group.style.cssText = `margin-bottom: 20px;`;

    const labelEl = document.createElement("label");
    labelEl.textContent = label;
    labelEl.setAttribute("for", id);
    labelEl.style.cssText = `
      display: block;
      font-size: 13px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 8px;
    `;

    const input = document.createElement("input");
    input.type = type;
    input.id = id;
    input.value = value;
    input.placeholder = placeholder;
    input.style.cssText = `
      width: 100%;
      padding: 10px 12px;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      font-family: inherit;
      font-size: 14px;
      color: #111827;
      background: #ffffff;
      transition: all 0.2s;
      box-sizing: border-box;
    `;
    input.onfocus = () => { input.style.borderColor = "#3b82f6"; input.style.boxShadow = "0 0 0 3px rgba(59, 130, 246, 0.1)"; };
    input.onblur = () => { input.style.borderColor = "#d1d5db"; input.style.boxShadow = "none"; };

    group.appendChild(labelEl);
    group.appendChild(input);
    return group;
  }

  async function testConnection(btn) {
    const originalText = btn.textContent;
    const settings = getSettings();

    btn.disabled = true;
    btn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="lg-spinner">
        <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
        <path d="M12 2a10 10 0 0 1 10 10" stroke-opacity="1"></path>
      </svg>
      Testing...
    `;

    try {
      const response = await new Promise((resolve, reject) => {
        GM_xmlhttpRequest({
          method: "GET",
          url: `${settings.backendEndpoint}/health`,
          timeout: 10000,
          onload: (res) => res.status === 200 ? resolve(res) : reject(new Error(`Status ${res.status}`)),
          onerror: (err) => reject(new Error("Network error")),
          ontimeout: () => reject(new Error("Timeout"))
        });
      });

      btn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22 4 12 14.01 9 11.01"></polyline>
        </svg>
        Connection Successful
      `;
      btn.style.borderColor = "#10b981";
      btn.style.color = "#10b981";
      showNotification("Backend connection successful!", "success");
    } catch (err) {
      btn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
        Connection Failed
      `;
      btn.style.borderColor = "#ef4444";
      btn.style.color = "#ef4444";
      showNotification(`Connection failed: ${err.message}`, "error");
    }

    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = originalText;
      btn.style.borderColor = "#d1d5db";
      btn.style.color = "#374151";
    }, 3000);
  }

  // ========== CONTEXT MENU ==========
  function createContextMenu() {
    const existing = document.getElementById("lg-context-menu");
    if (existing) existing.remove();

    const menu = document.createElement("div");
    menu.id = "lg-context-menu";
    menu.style.cssText = `
      position: fixed;
      display: none;
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
      z-index: 2147483647;
      min-width: 200px;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
    `;

    menu.innerHTML = `
      <div class="lg-context-menu-item" data-action="annotate-image" style="padding: 12px 16px; cursor: pointer; display: flex; align-items: center; gap: 12px; color: #111827;">
        <span style="font-size: 16px;">🏷️</span>
        <span style="font-weight: 500;">Annotate Image</span>
      </div>
      <div class="lg-context-menu-item" data-action="translate-text" style="padding: 12px 16px; cursor: pointer; display: flex; align-items: center; gap: 12px; color: #111827;">
        <span style="font-size: 16px;">🌐</span>
        <span style="font-weight: 500;">Translate Selection</span>
      </div>
      <hr style="margin: 6px 0; border: none; border-top: 1px solid #e5e7eb;">
      <div class="lg-context-menu-item" data-action="settings" style="padding: 12px 16px; cursor: pointer; display: flex; align-items: center; gap: 12px; color: #6b7280;">
        <span style="font-size: 16px;">⚙️</span>
        <span>Settings</span>
      </div>
    `;

    document.body.appendChild(menu);

    menu.querySelectorAll(".lg-context-menu-item").forEach(item => {
      item.addEventListener("click", (e) => {
        const action = item.dataset.action;
        hideContextMenu();

        if (action === "annotate-image" && contextMenuTarget && contextMenuMode === 'image') {
          handleAnnotateImage(contextMenuTarget.src, contextMenuTarget);
        } else if (action === "translate-text" && contextMenuMode === 'text') {
          handleTranslateText();
        } else if (action === "settings") {
          openSettingsDialog();
        }
      });

      item.addEventListener("mouseenter", () => {
        item.style.background = "#f3f4f6";
        if (item.dataset.action === "settings") item.style.color = "#111827";
      });

      item.addEventListener("mouseleave", () => {
        item.style.background = "transparent";
        if (item.dataset.action === "settings") item.style.color = "#6b7280";
      });
    });

    return menu;
  }

  let contextMenuTarget = null;
  let contextMenu = null;
  let contextMenuMode = null; // 'image' or 'text'
  let selectedTextForTranslation = null; // Store selected text before menu opens

  document.addEventListener("contextmenu", (e) => {
    const selectedText = window.getSelection()?.toString().trim();
    const hasTextSelection = selectedText && selectedText.length > 0;
    
    // Check if right-clicked on image
    if (e.target.tagName === "IMG") {
      e.preventDefault();
      contextMenuTarget = e.target;
      contextMenuMode = 'image';
      selectedTextForTranslation = null;
      showContextMenu(e.clientX, e.clientY);
    }
    // Check if there's a text selection
    else if (hasTextSelection) {
      e.preventDefault();
      contextMenuMode = 'text';
      selectedTextForTranslation = selectedText; // Save the selected text
      showContextMenu(e.clientX, e.clientY);
    }
  });

  function showContextMenu(x, y) {
    if (!contextMenu) {
      contextMenu = createContextMenu();
    }

    // Update menu items based on mode
    const annotateItem = contextMenu.querySelector('[data-action="annotate-image"]');
    const translateItem = contextMenu.querySelector('[data-action="translate-text"]');

    if (annotateItem && translateItem) {
      if (contextMenuMode === 'image') {
        annotateItem.style.display = 'flex';
        translateItem.style.display = 'none';
      } else {
        annotateItem.style.display = 'none';
        translateItem.style.display = 'flex';
      }
    }

    // Position menu
    const menuWidth = 200;
    const menuHeight = contextMenuMode === 'image' ? 160 : 120;

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

  function hideContextMenu() {
    if (contextMenu) {
      contextMenu.style.display = "none";
    }
  }

  // ========== NOTIFICATION SYSTEM ==========
  function showNotification(message, type = "info", duration = 3000) {
    const existing = document.querySelector(".lg-notification");
    if (existing) existing.remove();

    const notification = document.createElement("div");
    notification.className = "lg-notification";

    const colors = {
      success: { bg: "#10b981", icon: "M5 13l4 4L19 7" },
      error: { bg: "#ef4444", icon: "M6 18L18 6M6 6l12 12" },
      warning: { bg: "#f59e0b", icon: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" },
      info: { bg: "#3b82f6", icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" }
    };

    const color = colors[type] || colors.info;

    notification.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      padding: 14px 20px;
      background: #1f2937;
      color: white;
      border-radius: 12px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 14px;
      font-weight: 500;
      z-index: 2147483647;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
      display: flex;
      align-items: center;
      gap: 12px;
      animation: lgSlideIn 0.3s ease;
    `;

    notification.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="${color.bg}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;">
        <path d="${color.icon}"></path>
      </svg>
      <span>${message}</span>
    `;

    document.body.appendChild(notification);

    if (duration > 0) {
      setTimeout(() => {
        notification.style.opacity = "0";
        notification.style.transition = "opacity 0.3s ease, transform 0.3s ease";
        notification.style.transform = "translateX(100%)";
        setTimeout(() => notification.remove(), 300);
      }, duration);
    }

    return {
      dismiss: () => {
        notification.style.opacity = "0";
        notification.style.transition = "opacity 0.3s ease, transform 0.3s ease";
        notification.style.transform = "translateX(100%)";
        setTimeout(() => notification.remove(), 300);
      }
    };
  }

  function showPersistentNotification(message) {
    if (persistentNotification) {
      persistentNotification.dismiss();
    }
    persistentNotification = showNotification(message, "info", 0);
    return persistentNotification;
  }

  // ========== ANNOTATION HANDLERS ==========
  function handleAnnotateImage(imageUrl, imgElement) {
    if (isAnnotating) {
      showNotification("Annotation in progress, please wait...", "warning");
      return;
    }

    isAnnotating = true;
    const dismissNotification = showPersistentNotification("Annotating image...");

    fetchImageAndAnnotate(imageUrl)
      .then((response) => {
        dismissNotification.dismiss();
        isAnnotating = false;
        persistentNotification = null;

        if (response.success) {
          if (response.labels && response.labels.length > 0) {
            displayLabelsOnImage(response.labels, imgElement);
            showNotification(`Found ${response.labels.length} text region(s)`, "success");
          } else {
            showNotification("No text found in image", "info");
          }
        } else {
          showNotification(response.error || "Annotation failed", "error");
        }
      })
      .catch((err) => {
        console.error("[Image Annotator] Annotation error:", err);
        dismissNotification.dismiss();
        isAnnotating = false;
        persistentNotification = null;
        showNotification(err.message || "Annotation failed", "error");
      });
  }

  async function fetchImageAndAnnotate(imageUrl) {
    const settings = getSettings();
    const endpoint = settings.backendEndpoint || DEFAULT_SETTINGS.backendEndpoint;
    const authCode = settings.accessCode || "";
    const targetLang = settings.targetLanguage || "english";

    const blob = await fetchImageBlob(imageUrl);
    const resizedBlob = await resizeImageBlob(blob, 1000);

    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append("data", resizedBlob);

      const xhrUrl = `${endpoint}/image/annotate?translate=true&translate_language=${encodeURIComponent(targetLang)}`;

      GM_xmlhttpRequest({
        method: "POST",
        url: xhrUrl,
        headers: { "X-Auth-Code": authCode },
        data: formData,
        timeout: 600000,
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
        onerror: (err) => reject(new Error(`Network error: ${err.error || "Unknown error"}`)),
        ontimeout: () => reject(new Error("Annotation request timed out"))
      });
    });
  }

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
        onerror: (err) => reject(new Error(`Image fetch error: ${err.error || "Unknown error"}`)),
        ontimeout: () => reject(new Error("Image fetch timed out"))
      });
    });
  }

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

  // ========== LABEL OVERLAY ==========
  function displayLabelsOnImage(labels, imgElement) {
    removeExistingOverlay();

    const container = findPositionedContainer(imgElement);
    if (!container) {
      console.error("[Image Annotator] Could not find positioned container");
      return;
    }

    const overlay = document.createElement("div");
    overlay.className = "lg-label-container";
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
      labelDiv.className = "lg-label";
      labelDiv.dataset.index = index;
      labelDiv.style.cssText = `
        position: absolute;
        left: ${offsetX + label.x1 * imgRect.width}px;
        top: ${offsetY + label.y1 * imgRect.height}px;
        width: ${(label.x2 - label.x1) * imgRect.width}px;
        height: ${(label.y2 - label.y1) * imgRect.height}px;
        border: 2px solid #3b82f6;
        background: rgba(59, 130, 246, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        color: #1f2937;
        text-align: center;
        overflow: hidden;
        pointer-events: auto;
        cursor: pointer;
        box-sizing: border-box;
        border-radius: 6px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
      `;

      labelDiv.onmouseenter = function() {
        this.style.background = "rgba(59, 130, 246, 0.2)";
        this.style.borderColor = "#2563eb";
        this.style.boxShadow = "0 4px 16px rgba(59, 130, 246, 0.3)";
      };
      labelDiv.onmouseleave = function() {
        this.style.background = "rgba(59, 130, 246, 0.1)";
        this.style.borderColor = "#3b82f6";
        this.style.boxShadow = "0 2px 8px rgba(59, 130, 246, 0.2)";
      };

      if (label.text) {
        const textSpan = document.createElement("span");
        textSpan.textContent = label.text;
        textSpan.className = "lg-label-text";
        textSpan.dataset.fullText = label.text;
        textSpan.style.cssText = `
          padding: 4px 8px;
          background: rgba(59, 130, 246, 0.9);
          border-radius: 6px;
          font-size: 12px;
          max-width: 100%;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: #ffffff;
          font-weight: 600;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
          backdrop-filter: blur(4px);
        `;

        const tooltip = document.createElement("div");
        tooltip.className = "lg-label-tooltip";
        tooltip.textContent = label.text.replace(/\n/g, " ");
        const labelWidth = (label.x2 - label.x1) * imgRect.width;
        const labelHeight = (label.y2 - label.y1) * imgRect.height;
        tooltip.style.cssText = `
          position: absolute;
          background: rgba(255, 255, 255, 0.98);
          color: #1f2937;
          padding: 10px 14px;
          border-radius: 8px;
          font-size: 13px;
          line-height: 1.5;
          white-space: pre-wrap;
          word-break: break-word;
          max-width: ${Math.max(labelWidth, 240)}px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
          pointer-events: none;
          z-index: 2147483647;
          display: none;
          left: ${label.x1 * imgRect.width + (labelWidth / 2)}px;
          top: ${label.y1 * imgRect.height + (labelHeight / 2)}px;
          transform: translate(-50%, -50%);
          min-width: ${labelWidth}px;
          text-align: center;
          border: 1px solid #e5e7eb;
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

  function removeExistingOverlay() {
    const existing = document.querySelector(".lg-label-container");
    if (existing) existing.remove();
  }

  // ========== TRANSLATION HANDLERS ==========
  function handleTranslateText() {
    // Use the saved selected text
    const selectedText = selectedTextForTranslation;
    
    if (!selectedText) {
      showNotification("Please select some text to translate", "warning");
      return;
    }

    if (isTranslating) {
      showNotification("Translation in progress, please wait...", "warning");
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
          showNotification("Translation complete", "success");
          // Show translation in a nice popup instead of replacing inline
          showTranslationPopup(selectedText, response.translatedText);
        } else {
          showNotification(response.error || "Translation failed", "error");
        }
      })
      .catch((err) => {
        dismissNotification.dismiss();
        isTranslating = false;
        persistentNotification = null;
        showNotification(err.message || "Translation failed", "error");
      });
  }

  function showTranslationPopup(original, translated) {
    const content = document.createElement("div");
    content.style.cssText = `
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;

    const originalSection = document.createElement("div");
    originalSection.style.cssText = `margin-bottom: 16px;`;
    originalSection.innerHTML = `
      <div style="font-size: 11px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">Original</div>
      <div style="background: #f3f4f6; padding: 12px; border-radius: 8px; color: #1f2937; font-size: 14px; line-height: 1.5;">${escapeHtml(original)}</div>
    `;

    const translatedSection = document.createElement("div");
    translatedSection.innerHTML = `
      <div style="font-size: 11px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px;">Translation</div>
      <div style="background: rgba(59, 130, 246, 0.08); padding: 12px; border-radius: 8px; color: #1f2937; font-size: 14px; line-height: 1.5; border: 1px solid rgba(59, 130, 246, 0.2);">${escapeHtml(translated)}</div>
    `;

    content.appendChild(originalSection);
    content.appendChild(translatedSection);

    createModal(
      "🌐 Translation",
      content,
      [
        { label: "Close", primary: true, onClick: () => {} }
      ]
    );
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

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
        timeout: 300000,
        onload: (response) => {
          if (response.status === 401) {
            resolve({ success: false, error: "Authentication failed. Please check your access code." });
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
        onerror: (err) => reject(new Error(`Network error: ${err.error || "Unknown error"}`)),
        ontimeout: () => reject(new Error("Translation request timed out"))
      });
    });
  }

  console.log("[Image Annotator] Tampermonkey script initialized (v2.0 - Professional Edition)");
})();
