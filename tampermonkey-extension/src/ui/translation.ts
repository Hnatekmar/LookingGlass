import { showNotification } from './notification';
import { translateText as apiTranslateText } from '../core/api';

let isTranslating = false;
let translateTooltip: HTMLDivElement | null = null;
let dismissTimer: ReturnType<typeof setTimeout> | null = null;
let selectionDebounce: ReturnType<typeof setTimeout> | null = null;

const MIN_TEXT_LENGTH = 3;
const TOOLTIP_DURATION = 8000;

/**
 * Set up auto-translate on text selection.
 * Call once during initialization.
 */
export function setupAutoTranslate(): void {
  document.addEventListener("mouseup", onMouseUp);
  document.addEventListener("click", onDocumentClick, { capture: true });
  document.addEventListener("scroll", dismissTooltip, { capture: true, passive: true });
}

function onMouseUp(): void {
  const selection = window.getSelection();
  const selectedText = selection?.toString().trim();

  // Clear any pending debounce
  if (selectionDebounce) {
    clearTimeout(selectionDebounce);
    selectionDebounce = null;
  }

  // Dismiss tooltip if selection is cleared
  if (!selectedText || selectedText.length < MIN_TEXT_LENGTH) {
    dismissTooltip();
    return;
  }

  // Don't auto-translate inside our own UI elements
  const target = document.activeElement;
  if (target && target.closest(".lg-modal-overlay, .lg-label-container, .lg-translate-tooltip")) {
    return;
  }

  // Debounce: wait 400ms after user stops selecting before translating
  selectionDebounce = setTimeout(() => {
    selectionDebounce = null;
    doAutoTranslate(selectedText, selection!);
  }, 400);
}

function onDocumentClick(e: MouseEvent): void {
  // Dismiss tooltip when clicking outside it
  if (translateTooltip && !translateTooltip.contains(e.target as Node)) {
    dismissTooltip();
  }
}

async function doAutoTranslate(text: string, selection: Selection): Promise<void> {
  if (isTranslating) return;
  isTranslating = true;

  try {
    const response = await apiTranslateText(text);
    if (response.success && response.translatedText) {
      showTranslateInline(text, response.translatedText, selection);
    }
  } catch {
    // Silently fail for auto-translate — don't spam errors
  } finally {
    isTranslating = false;
  }
}

/**
 * Show translated text as a small floating tooltip near the selection.
 */
function showTranslateInline(original: string, translated: string, selection: Selection): void {
  // Remove any existing tooltip
  dismissTooltip();

  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();

  // If selection is off-screen or empty, don't show
  if (rect.width === 0 && rect.height === 0) return;

  translateTooltip = document.createElement("div");
  translateTooltip.className = "lg-translate-tooltip";
  translateTooltip.style.cssText = `
    position: fixed;
    left: ${rect.left + rect.width / 2}px;
    top: ${rect.bottom + 8}px;
    transform: translateX(-50%);
    background: #1f2937;
    color: #ffffff;
    padding: 10px 16px;
    border-radius: 10px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 13px;
    line-height: 1.5;
    max-width: 400px;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
    z-index: 2147483647;
    pointer-events: auto;
    animation: lgFadeIn 0.2s ease;
    word-break: break-word;
  `;

  // Content: translated text with a small label
  translateTooltip.innerHTML = `
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
      <span style="font-size: 11px; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em;">Translation</span>
      <span style="font-size: 11px; color: #6b7280;">·</span>
      <span style="font-size: 11px; color: #6b7280; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${escapeHtml(original.replace(/\n/g, " ").substring(0, 60))}${original.length > 60 ? '…' : ''}</span>
    </div>
    <div style="font-size: 14px; font-weight: 500; color: #ffffff;">${escapeHtml(translated)}</div>
  `;

  // Ensure tooltip stays within viewport
  document.body.appendChild(translateTooltip);

  // Check right edge
  const tooltipRect = translateTooltip.getBoundingClientRect();
  if (tooltipRect.right > window.innerWidth - 16) {
    translateTooltip.style.left = `${window.innerWidth - tooltipRect.width - 16}px`;
    translateTooltip.style.transform = "none";
  }
  if (tooltipRect.left < 16) {
    translateTooltip.style.left = "16px";
    translateTooltip.style.transform = "none";
  }
  // If tooltip would go below viewport, position above the selection
  if (tooltipRect.bottom > window.innerHeight - 16) {
    translateTooltip.style.top = `${rect.top - tooltipRect.height - 8}px`;
  }

  // Auto-dismiss after duration
  if (dismissTimer) clearTimeout(dismissTimer);
  dismissTimer = setTimeout(dismissTooltip, TOOLTIP_DURATION);
}

function dismissTooltip(): void {
  if (dismissTimer) {
    clearTimeout(dismissTimer);
    dismissTimer = null;
  }
  if (translateTooltip) {
    translateTooltip.remove();
    translateTooltip = null;
  }
}

/**
 * Handle Translate Selection from context menu.
 * Uses the same inline tooltip instead of a modal.
 */
export async function handleTranslateText(): Promise<void> {
  const selection = window.getSelection();
  const selectedText = selection?.toString().trim();

  if (!selectedText) {
    showNotification("Please select some text to translate", "warning");
    return;
  }

  if (isTranslating) {
    showNotification("Translation in progress, please wait...", "warning");
    return;
  }

  isTranslating = true;
  const notify = showNotification("Translating...", "info", 0);

  try {
    const response = await apiTranslateText(selectedText);
    notify.dismiss();

    if (response.success && response.translatedText) {
      showTranslateInline(selectedText, response.translatedText, selection!);
    } else {
      showNotification(response.error || "Translation failed", "error");
    }
  } catch (err: any) {
    notify.dismiss();
    showNotification(err.message || "Translation failed", "error");
  } finally {
    isTranslating = false;
  }
}

function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
