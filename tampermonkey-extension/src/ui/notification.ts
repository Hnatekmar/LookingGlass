import type { NotificationType } from '../types';

let persistentNotification: { dismiss: () => void } | null = null;

const COLORS = {
  success: { bg: "#10b981", icon: "M5 13l4 4L19 7" },
  error: { bg: "#ef4444", icon: "M6 18L18 6M6 6l12 12" },
  warning: { bg: "#f59e0b", icon: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" },
  info: { bg: "#3b82f6", icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" }
};

export function showNotification(message: string, type: NotificationType = "info", duration: number = 3000): { dismiss: () => void } {
  const existing = document.querySelector(".lg-notification");
  if (existing) existing.remove();

  const notification = document.createElement("div");
  notification.className = "lg-notification";

  const color = COLORS[type] || COLORS.info;

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
    <span>${escapeHtml(message)}</span>
  `;

  document.body.appendChild(notification);

  const dismiss = () => {
    notification.style.opacity = "0";
    notification.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    notification.style.transform = "translateX(100%)";
    setTimeout(() => notification.remove(), 300);
  };

  if (duration > 0) {
    setTimeout(() => {
      dismiss();
    }, duration);
  }

  return { dismiss };
}

export function showPersistentNotification(message: string): { dismiss: () => void } {
  if (persistentNotification) {
    persistentNotification.dismiss();
  }
  persistentNotification = showNotification(message, "info", 0);
  return persistentNotification;
}

export function dismissPersistentNotification(): void {
  if (persistentNotification) {
    persistentNotification.dismiss();
    persistentNotification = null;
  }
}

function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
