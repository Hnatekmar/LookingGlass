import { getSettings, saveSettings, getDefaults, validateEndpoint } from '../core/settings';
import { createModal } from './modal';
import { showNotification } from './notification';
import { testConnection } from '../core/api';

export function openSettingsDialog(): void {
  const settings = getSettings();

  const content = document.createElement("div");
  content.style.cssText = `
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  `;

  // Endpoint field with validation
  const endpointGroup = createFormField("Backend Endpoint", "text", settings.backendEndpoint, "Enter your backend API endpoint", "endpoint", (value) => {
    const input = document.getElementById("endpoint") as HTMLInputElement;
    const isValid = validateEndpoint(value);
    input.style.borderColor = isValid ? "#d1d5db" : "#ef4444";
    if (!isValid && value.length > 0) {
      input.style.boxShadow = "0 0 0 3px rgba(239, 68, 68, 0.1)";
    } else {
      input.style.boxShadow = "none";
    }
  });
  content.appendChild(endpointGroup);

  // Access Code field
  const accessCodeGroup = createFormField("Access Code", "password", settings.accessCode, "Enter your access code for authentication", "accessCode");
  content.appendChild(accessCodeGroup);

  // Target Language field
  const languageGroup = createFormField("Target Language", "text", settings.targetLanguage, "Language for translations (e.g., english, spanish)", "targetLanguage");
  content.appendChild(languageGroup);

  // Auto Translate toggle
  const autoTranslateGroup = createToggleField(
    "Auto-Translate Selection",
    "Automatically translate selected text on any webpage",
    settings.autoTranslate ?? true,
    "autoTranslate"
  );
  content.appendChild(autoTranslateGroup);

  // Test connection button
  const testSection = document.createElement("div");
  testSection.style.cssText = `
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #e5e7eb;
  `;

  const testBtn = createTestButton();
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
          const endpointInput = document.getElementById("endpoint") as HTMLInputElement;
          const endpointValue = endpointInput.value.trim();
          
          if (endpointValue && !validateEndpoint(endpointValue)) {
            showNotification("Please enter a valid URL for the backend endpoint", "error");
            endpointInput.focus();
            return;
          }

          const newSettings = {
            backendEndpoint: endpointValue || getDefaults().backendEndpoint,
            accessCode: (document.getElementById("accessCode") as HTMLInputElement).value,
            targetLanguage: (document.getElementById("targetLanguage") as HTMLInputElement).value || "english",
            autoTranslate: (document.getElementById("autoTranslate") as HTMLInputElement).checked
          };
          saveSettings(newSettings);
          showNotification("Settings saved successfully", "success");
        }
      }
    ]
  );
}

function createFormField(label: string, type: string, value: string, placeholder: string, id: string, onInput?: (value: string) => void): HTMLDivElement {
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
  if (onInput) {
    input.oninput = (e) => onInput((e.target as HTMLInputElement).value);
  }

  group.appendChild(labelEl);
  group.appendChild(input);
  return group;
}

function createTestButton(): HTMLButtonElement {
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
  testBtn.onclick = () => handleTestConnection(testBtn);

  const testIcon = document.createElement("span");
  testIcon.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
      <polyline points="22 4 12 14.01 9 11.01"></polyline>
    </svg>
  `;
  testBtn.insertBefore(testIcon, testBtn.firstChild);

  return testBtn;
}

async function handleTestConnection(btn: HTMLButtonElement): Promise<void> {
  const originalText = btn.textContent;

  btn.disabled = true;
  btn.innerHTML = `
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="lg-spinner">
      <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
      <path d="M12 2a10 10 0 0 1 10 10" stroke-opacity="1"></path>
    </svg>
    Testing...
  `;

  const result = await testConnection();

  if (result.success) {
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
  } else {
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
    showNotification(`Connection failed: ${result.error}`, "error");
  }

  setTimeout(() => {
    btn.disabled = false;
    btn.textContent = originalText;
    btn.style.borderColor = "#d1d5db";
    btn.style.color = "#374151";
  }, 3000);
}

function createToggleField(label: string, description: string, checked: boolean, id: string): HTMLDivElement {
  const group = document.createElement("div");
  group.style.cssText = `margin-bottom: 20px;`;

  const labelRow = document.createElement("div");
  labelRow.style.cssText = `
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  `;

  const textSide = document.createElement("div");
  textSide.style.cssText = `flex: 1;`;

  const labelEl = document.createElement("div");
  labelEl.textContent = label;
  labelEl.style.cssText = `
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 2px;
  `;

  const descEl = document.createElement("div");
  descEl.textContent = description;
  descEl.style.cssText = `
    font-size: 12px;
    color: #6b7280;
  `;

  textSide.appendChild(labelEl);
  textSide.appendChild(descEl);

  // Toggle switch
  const toggle = document.createElement("label");
  toggle.style.cssText = `
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
    flex-shrink: 0;
    cursor: pointer;
  `;

  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.id = id;
  checkbox.checked = checked;
  checkbox.style.cssText = `
    opacity: 0;
    width: 0;
    height: 0;
    position: absolute;
  `;

  const slider = document.createElement("span");
  slider.style.cssText = `
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: ${checked ? '#3b82f6' : '#d1d5db'};
    transition: 0.3s;
    border-radius: 24px;
  `;

  const knob = document.createElement("span");
  knob.style.cssText = `
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background: white;
    transition: 0.3s;
    border-radius: 50%;
    transform: ${checked ? 'translateX(20px)' : 'translateX(0)'};
  `;

  checkbox.onchange = () => {
    slider.style.background = checkbox.checked ? '#3b82f6' : '#d1d5db';
    knob.style.transform = checkbox.checked ? 'translateX(20px)' : 'translateX(0)';
  };

  slider.appendChild(knob);
  toggle.appendChild(checkbox);
  toggle.appendChild(slider);

  labelRow.appendChild(textSide);
  labelRow.appendChild(toggle);
  group.appendChild(labelRow);

  return group;
}

