import { showNotification } from './notification';
import { createModal } from './modal';
import { translateText as apiTranslateText } from '../core/api';
import { getContextMenuState } from '../ui/context-menu';

let isTranslating = false;

export function handleTranslateText(): void {
  const state = getContextMenuState();
  const selectedText = state.selectedText;
  
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

  apiTranslateText(selectedText)
    .then((response) => {
      dismissNotification.dismiss();
      isTranslating = false;

      if (response.success) {
        showNotification("Translation complete", "success");
        showTranslationPopup(selectedText, response.translatedText!);
      } else {
        showNotification(response.error || "Translation failed", "error");
      }
    })
    .catch((err) => {
      dismissNotification.dismiss();
      isTranslating = false;
      showNotification(err.message || "Translation failed", "error");
    });
}

function showTranslationPopup(original: string, translated: string): void {
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

function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function showPersistentNotification(message: string): { dismiss: () => void } {
  const notification = showNotification(message, "info", 0);
  return notification;
}
