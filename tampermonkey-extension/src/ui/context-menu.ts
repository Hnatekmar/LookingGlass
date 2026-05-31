import type { ContextMenuState } from '../types';
import { openSettingsDialog } from '../ui/settings';
import { handleTranslateText } from './translation';
import { handleAnnotateImage } from '../handlers/annotation';

let contextMenu: HTMLDivElement | null = null;
let contextMenuState: ContextMenuState = {
  target: null,
  mode: null,
  selectedText: null
};

export function setupContextMenu(): void {
  document.addEventListener("contextmenu", (e) => {
    const selectedText = window.getSelection()?.toString().trim();
    const hasTextSelection = selectedText && selectedText.length > 0;
    
    if (e.target.tagName === "IMG") {
      e.preventDefault();
      contextMenuState = {
        target: e.target,
        mode: 'image',
        selectedText: null
      };
      showContextMenu(e.clientX, e.clientY);
    }
    else if (hasTextSelection) {
      e.preventDefault();
      contextMenuState = {
        target: null,
        mode: 'text',
        selectedText
      };
      showContextMenu(e.clientX, e.clientY);
    }
  });

  // Hide menu on scroll
  document.addEventListener("scroll", hideContextMenu, { capture: true, passive: true });
  
  // Hide menu on Escape
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      hideContextMenu();
    }
  });
}

function createContextMenu(): HTMLDivElement {
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
      e.stopPropagation();
      const action = (item as HTMLElement).dataset.action;
      hideContextMenu();

      if (action === "annotate-image" && contextMenuState.mode === 'image' && contextMenuState.target) {
        const imgElement = contextMenuState.target as HTMLImageElement;
        handleAnnotateImage(imgElement.src, imgElement);
      } else if (action === "translate-text" && contextMenuState.mode === 'text') {
        handleTranslateText();
      } else if (action === "settings") {
        openSettingsDialog();
      }
    });

    item.addEventListener("mouseenter", () => {
      item.style.background = "#f3f4f6";
      if ((item as HTMLElement).dataset.action === "settings") {
        item.style.color = "#111827";
      }
    });

    item.addEventListener("mouseleave", () => {
      item.style.background = "transparent";
      if ((item as HTMLElement).dataset.action === "settings") {
        item.style.color = "#6b7280";
      }
    });
  });

  return menu;
}

function showContextMenu(x: number, y: number): void {
  if (!contextMenu) {
    contextMenu = createContextMenu();
  }

  const annotateItem = contextMenu.querySelector('[data-action="annotate-image"]');
  const translateItem = contextMenu.querySelector('[data-action="translate-text"]');

  if (annotateItem && translateItem) {
    if (contextMenuState.mode === 'image') {
      annotateItem.style.display = 'flex';
      translateItem.style.display = 'none';
    } else {
      annotateItem.style.display = 'none';
      translateItem.style.display = 'flex';
    }
  }

  const menuWidth = 200;
  const menuHeight = contextMenuState.mode === 'image' ? 160 : 120;

  if (x + menuWidth > window.innerWidth) {
    x = window.innerWidth - menuWidth - 10;
  }
  if (y + menuHeight > window.innerHeight) {
    y = window.innerHeight - menuHeight - 10;
  }

  contextMenu.style.left = x + "px";
  contextMenu.style.top = y + "px";
  contextMenu.style.display = "block";

  const hideOnNextClick = (ev: MouseEvent) => {
    if (!contextMenu?.contains(ev.target as Node)) {
      hideContextMenu();
      document.removeEventListener("click", hideOnNextClick);
    }
  };
  setTimeout(() => {
    document.addEventListener("click", hideOnNextClick);
  }, 100);
}

export function hideContextMenu(): void {
  if (contextMenu) {
    contextMenu.style.display = "none";
  }
}

export function resetContextMenuState(): void {
  contextMenuState = {
    target: null,
    mode: null,
    selectedText: null
  };
}

export function getContextMenuState(): ContextMenuState {
  return { ...contextMenuState };
}
