import { injectBaseStyles } from './ui/styles';
import { setupContextMenu } from './ui/context-menu';
import { openSettingsDialog } from './ui/settings';

export function initialize(): void {
  console.log("[Image Annotator] Tampermonkey script loading...");

  // Inject base styles
  injectBaseStyles();

  // Register menu command for settings
  GM_registerMenuCommand("⚙️ Image Annotator Settings", openSettingsDialog);

  // Setup context menu
  setupContextMenu();

  console.log("[Image Annotator] Tampermonkey script initialized (v2.0 - TypeScript Edition)");
}

// Start the application
initialize();
