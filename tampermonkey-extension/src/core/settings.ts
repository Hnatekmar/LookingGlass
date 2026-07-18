import type { Settings } from '../types';

const DEFAULT_SETTINGS: Settings = {
  backendEndpoint: "http://localhost:8000/v1",
  accessCode: "",
  targetLanguage: "english",
  autoAnnotate: false,
  autoTranslate: true,
  qualityMode: "balanced"
};

export function getSettings(): Settings {
  return {
    backendEndpoint: GM_getValue("backendEndpoint", DEFAULT_SETTINGS.backendEndpoint),
    accessCode: GM_getValue("accessCode", DEFAULT_SETTINGS.accessCode),
    targetLanguage: GM_getValue("targetLanguage", DEFAULT_SETTINGS.targetLanguage),
    autoAnnotate: GM_getValue("autoAnnotate", DEFAULT_SETTINGS.autoAnnotate),
    autoTranslate: GM_getValue("autoTranslate", DEFAULT_SETTINGS.autoTranslate),
    qualityMode: GM_getValue("qualityMode", DEFAULT_SETTINGS.qualityMode)
  };
}

export function saveSettings(settings: Partial<Settings>): void {
  Object.entries(settings).forEach(([key, value]) => {
    GM_setValue(key, value);
  });
}

export function getDefaults(): Settings {
  return { ...DEFAULT_SETTINGS };
}

export function validateEndpoint(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}
