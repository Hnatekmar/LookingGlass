export interface ModalAction {
  label: string;
  primary: boolean;
  onClick?: () => void;
}

export function createModal(title: string, content: HTMLElement, actions: ModalAction[]): { overlay: HTMLDivElement; modal: HTMLDivElement; content: HTMLDivElement } {
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

  // Close on Escape key
  const handleEscape = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      removeExistingModal();
      document.removeEventListener('keydown', handleEscape);
    }
  };
  document.addEventListener('keydown', handleEscape);

  return { overlay, modal, content: contentEl };
}

export function removeExistingModal(): void {
  const existing = document.querySelector(".lg-modal-overlay");
  if (existing) existing.remove();
}
