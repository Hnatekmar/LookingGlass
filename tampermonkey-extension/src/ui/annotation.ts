import type { Label } from '../types';
import { showNotification } from './notification';

export function displayLabelsOnImage(labels: Label[], imgElement: HTMLImageElement): void {
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
    const labelDiv = createLabelElement(label, index, imgRect, offsetX, offsetY, overlay);
    overlay.appendChild(labelDiv);
  });

  container.style.position = container.style.position || "relative";
  container.appendChild(overlay);
}

/**
 * Display labels progressively as they arrive from the streaming endpoint.
 * On the first batch, creates a fresh overlay. Subsequent batches add to it.
 */
export function displayLabelsProgressive(
  labels: Label[],
  imgElement: HTMLImageElement,
  isFirstBatch: boolean,
): void {
  if (isFirstBatch) {
    removeExistingOverlay();
  }

  const container = findPositionedContainer(imgElement);
  if (!container) {
    console.error("[Image Annotator] Could not find positioned container");
    return;
  }

  let overlay = document.querySelector(".lg-label-container") as HTMLElement | null;
  if (!overlay) {
    overlay = document.createElement("div");
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
    container.style.position = container.style.position || "relative";
    container.appendChild(overlay);
  }

  const imgRect = imgElement.getBoundingClientRect();
  const containerRect = container.getBoundingClientRect();
  const offsetX = imgRect.left - containerRect.left;
  const offsetY = imgRect.top - containerRect.top;

  // Count existing labels to assign unique indices
  const existingCount = overlay.querySelectorAll(".lg-label").length;

  labels.forEach((label, i) => {
    const labelDiv = createLabelElement(label, existingCount + i, imgRect, offsetX, offsetY, overlay!);
    overlay!.appendChild(labelDiv);
  });
}

function createLabelElement(label: Label, index: number, imgRect: DOMRect, offsetX: number, offsetY: number, overlay: HTMLElement): HTMLDivElement {
  const labelDiv = document.createElement("div");
  labelDiv.className = "lg-label";
  labelDiv.dataset.index = String(index);
  
  const left = offsetX + label.x1 * imgRect.width;
  const top = offsetY + label.y1 * imgRect.height;
  const width = (label.x2 - label.x1) * imgRect.width;
  const height = (label.y2 - label.y1) * imgRect.height;

  labelDiv.style.cssText = `
    position: absolute;
    left: ${left}px;
    top: ${top}px;
    width: ${width}px;
    height: ${height}px;
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
    // Update text span background too
    const textSpan = this.querySelector(".lg-label-text");
    if (textSpan) {
      textSpan.style.background = "rgba(59, 130, 246, 1)";
    }
  };
  labelDiv.onmouseleave = function() {
    this.style.background = "rgba(59, 130, 246, 0.1)";
    this.style.borderColor = "#3b82f6";
    this.style.boxShadow = "0 2px 8px rgba(59, 130, 246, 0.2)";
    // Reset text span background
    const textSpan = this.querySelector(".lg-label-text");
    if (textSpan) {
      textSpan.style.background = "rgba(59, 130, 246, 0.9)";
    }
  };

  if (label.text) {
    const textSpan = createLabelText(label.text, width);
    const tooltip = createLabelTooltip(label.text, width);
    
    labelDiv.addEventListener("mouseenter", (e) => {
      e.stopPropagation();
      // Dynamically calculate tooltip position relative to overlay container
      const labelRect = labelDiv.getBoundingClientRect();
      const containerRect = overlay.getBoundingClientRect();
      const relativeLeft = labelRect.left - containerRect.left + (labelRect.width / 2);
      const relativeTop = labelRect.top - containerRect.top + (labelRect.height / 2);
      tooltip.style.left = `${relativeLeft}px`;
      tooltip.style.top = `${relativeTop}px`;
      tooltip.style.transform = "translate(-50%, -50%)";
      tooltip.style.display = "block";
    });

    labelDiv.addEventListener("mouseleave", (e) => {
      e.stopPropagation();
      tooltip.style.display = "none";
    });

    labelDiv.appendChild(textSpan);
    // Append tooltip to overlay, not labelDiv, for proper positioning
    overlay.appendChild(tooltip);
  }

  labelDiv.addEventListener("click", (e) => {
    e.stopPropagation();
    overlay.remove();
  });

  return labelDiv;
}

function createLabelText(text: string, labelWidth: number): HTMLSpanElement {
  const textSpan = document.createElement("span");
  textSpan.textContent = text;
  textSpan.className = "lg-label-text";
  textSpan.dataset.fullText = text;
  textSpan.style.cssText = `
    padding: 4px 8px;
    background: rgba(59, 130, 246, 0.9);
    border-radius: 6px;
    font-size: 12px;
    max-width: calc(100% - 16px);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #ffffff;
    font-weight: 600;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(4px);
  `;
  return textSpan;
}

function createLabelTooltip(text: string, labelWidth: number): HTMLDivElement {
  const tooltip = document.createElement("div");
  tooltip.className = "lg-label-tooltip";
  tooltip.textContent = text.replace(/\n/g, " ");
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
    min-width: ${labelWidth}px;
    text-align: center;
    border: 1px solid #e5e7eb;
  `;
  return tooltip;
}

function findPositionedContainer(element: HTMLElement): HTMLElement | null {
  let current: HTMLElement | null = element.parentElement;
  while (current && current !== document.body) {
    const position = window.getComputedStyle(current).position;
    if (position === "relative" || position === "absolute" || position === "fixed") {
      return current;
    }
    current = current.parentElement;
  }
  return document.body;
}

export function removeExistingOverlay(): void {
  const existing = document.querySelector(".lg-label-container");
  if (existing) existing.remove();
}
