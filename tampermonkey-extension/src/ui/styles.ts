export function injectBaseStyles(): void {
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
}
