// Options page script for Image Annotator Chrome Extension

// Default settings
const DEFAULT_SETTINGS = {
    backendEndpoint: 'http://localhost:8000',
    translateEndpoint: '/translate',
    annotateEndpoint: '/image/annotate',
    targetLanguage: 'english',
    accessCode: ''
};

// Load settings from Chrome storage
function loadSettings() {
    chrome.storage.sync.get(DEFAULT_SETTINGS, (settings) => {
        document.getElementById('backendEndpoint').value = settings.backendEndpoint;
        document.getElementById('translateEndpoint').value = settings.translateEndpoint;
        document.getElementById('annotateEndpoint').value = settings.annotateEndpoint;
        document.getElementById('targetLanguage').value = settings.targetLanguage;
        document.getElementById('accessCode').value = settings.accessCode || '';

        // Set the access code page link
        const backendUrl = settings.backendEndpoint || DEFAULT_SETTINGS.backendEndpoint;
        document.getElementById('getAccessCodeLink').href = `${backendUrl}/auth/access-code`;
    });
}

function saveSettings() {
    const settings = {
        backendEndpoint: document.getElementById("backendEndpoint").value.trim(),
        translateEndpoint: document.getElementById("translateEndpoint").value.trim(),
        annotateEndpoint: document.getElementById("annotateEndpoint").value.trim(),
        targetLanguage: document.getElementById("targetLanguage").value,
        accessCode: document.getElementById("accessCode").value.trim()
    };
    
    // Validate backend endpoint
    if (!settings.backendEndpoint) {
        showSaveMessage("Backend endpoint is required", "error");
        return;
    }
    
    // Ensure backend endpoint has protocol
    if (!settings.backendEndpoint.startsWith('http://') && !settings.backendEndpoint.startsWith('https://')) {
        showSaveMessage('Backend endpoint must include protocol (http:// or https://)', 'error');
        return;
    }
    
    console.log('Saving settings:', settings);  // Debug log
    chrome.storage.sync.set(settings, () => {
        if (chrome.runtime.lastError) {
            console.error('Chrome storage error:', chrome.runtime.lastError);  // Debug log
            showSaveMessage('Error saving settings: ' + chrome.runtime.lastError.message, 'error');
        } else {
            console.log('Settings saved successfully');  // Debug log
            showSaveMessage('Settings saved successfully!', 'success');
            
            // Broadcast settings update to all tabs
            chrome.tabs.query({}, (tabs) => {
                tabs.forEach(tab => {
                    chrome.tabs.sendMessage(tab.id, {
                        action: 'settings-updated',
                        settings: settings
                    }).catch(() => {
                        // Tab may not have content script loaded
                    });
                });
            });
        }
    });
}

// Reset settings to defaults
function resetSettings() {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
        chrome.storage.sync.set(DEFAULT_SETTINGS, () => {
            loadSettings();
            showSaveMessage('Settings reset to defaults', 'success');
        });
    }
}

// Show save message
function showSaveMessage(message, type) {
    const messageEl = document.getElementById('saveMessage');
    messageEl.textContent = message;
    messageEl.className = type;
    
    setTimeout(() => {
        messageEl.className = '';
    }, 3000);
}

// Test connection to backend
function testConnection() {
    const backendEndpoint = document.getElementById('backendEndpoint').value.trim();
    const testResult = document.getElementById('testResult');
    
    if (!backendEndpoint) {
        testResult.textContent = 'Please enter a backend endpoint URL';
        testResult.className = 'test-result error';
        return;
    }
    
    testResult.textContent = 'Testing connection...';
    testResult.className = 'test-result';
    
    // Test by trying to reach a simple endpoint
    fetch(`${backendEndpoint}/health`)
        .then(response => {
            if (response.ok) {
                testResult.textContent = '✓ Connection successful! Backend is reachable.';
                testResult.className = 'test-result success';
            } else {
                testResult.textContent = '⚠ Backend responded with status: ' + response.status;
                testResult.className = 'test-result error';
            }
        })
        .catch(error => {
            testResult.textContent = '✗ Connection failed: ' + error.message + '\n\nMake sure your backend is running and the URL is correct.';
            testResult.className = 'test-result error';
        });
}

// Get full endpoint URL
function getFullEndpoint(endpointPath) {
    const backendEndpoint = document.getElementById('backendEndpoint').value.trim();
    const basePath = backendEndpoint.replace(/\/$/, ''); // Remove trailing slash
    const endpoint = endpointPath.replace(/^\//, ''); // Remove leading slash
    return `${basePath}/${endpoint}`;
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    
    // Save button
    document.getElementById('saveBtn').addEventListener('click', saveSettings);
    
    // Reset button
    document.getElementById('resetBtn').addEventListener('click', resetSettings);
    
    // Test connection button
    document.getElementById('testConnection').addEventListener('click', testConnection);

    // Get access code button
    document.getElementById('getAccessCodeBtn').addEventListener('click', () => {
        const backendUrl = document.getElementById('backendEndpoint').value.trim() || DEFAULT_SETTINGS.backendEndpoint;
        const accessCodePage = `${backendUrl}/auth/access-code`;
        window.open(accessCodePage, '_blank');
    });

    // Preset endpoint buttons
    
    // Save on Enter key in input fields
    document.querySelectorAll('input[type="text"], input[type="url"]').forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                saveSettings();
            }
        });
    });
});

// Expose helper functions for other scripts
window.getFullEndpoint = getFullEndpoint;
window.DEFAULT_SETTINGS = DEFAULT_SETTINGS;
