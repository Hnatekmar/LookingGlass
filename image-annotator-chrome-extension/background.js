// Background script for Image Annotator Chrome Extension

// Default settings
const DEFAULT_SETTINGS = {
    backendEndpoint: 'http://localhost:8000',
    translateEndpoint: '/translate',
    annotateEndpoint: '/image/annotate',
    targetLanguage: 'english',
    accessCode: ''
};

// Load settings from storage
function getSettings() {
    return new Promise((resolve) => {
        chrome.storage.sync.get(DEFAULT_SETTINGS, resolve);
    });
}

// Build full URL for endpoint
function buildEndpointUrl(endpointPath, settings) {
    const basePath = settings.backendEndpoint.replace(/\/$/, ''); // Remove trailing slash
    const endpoint = endpointPath.replace(/^\//, ''); // Remove leading slash
    return `${basePath}/${endpoint}`;
}

// Make authenticated fetch request
async function authenticatedFetch(url, options = {}) {
    const settings = await getSettings();
    
    const headers = options.headers || {};
    if (settings.accessCode) {
        headers["X-Auth-Code"] = settings.accessCode;
    }
    
    const response = await fetch(url, { ...options, headers });
    
    // Handle 401 Unauthorized
    if (response.status === 401) {
        throw new Error('Authentication required. Please configure your access code in extension settings.');
    }
    
    return response;
}

// Create context menu items when extension is installed
chrome.runtime.onInstalled.addListener(async () => {
    // Create context menu for images
    chrome.contextMenus.create({
        id: "translate-image",
        title: "Annotate Image",
        contexts: ["image"],
        documentUrlPatterns: ["https://*/*"]
    });

    // Create context menu for text selection
    chrome.contextMenus.create({
        id: "translate-text",
        title: "Translate Selection",
        contexts: ["selection"],
        documentUrlPatterns: ["https://*/*"]
    });

    console.log("Image Annotator context menus created");
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    const settings = await getSettings();
    
    if (info.menuItemId === "translate-image" && info.srcUrl) {
        console.log('Attempting to annotate image:', info.srcUrl);
        console.log('Tab ID:', tab.id, 'URL:', tab.url);
        
        // Send message to content script to annotate the image
        chrome.tabs.sendMessage(tab.id, {
            action: "annotate-image",
            imageUrl: info.srcUrl,
            targetElement: {
                src: info.srcUrl
            },
            settings: settings
        }).catch(error => {
            console.error('❌ Failed to send message to content script:', error);
            console.log('👉 Possible causes:');
            console.log('   - Page was loaded before extension was reloaded');
            console.log('   - Page URL is not https:// (current manifest only supports https)');
            console.log('   - Content script failed to inject');
            console.log('👉 Solution: Reload the page (Ctrl+R) after reloading the extension');
        });
    } else if (info.menuItemId === "translate-text" && info.selectionText) {
        // Send message to content script to translate text
        chrome.tabs.sendMessage(tab.id, {
            action: "translate-text",
            text: info.selectionText,
            settings: settings
        }).catch(error => {
            console.error('Failed to send message to content script:', error);
            console.log('Hint: Reload the page to load the content script');
        });
    }
});

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log("Background received message:", request.action);
    
    if (request.action === "fetch-image-blob") {
        // Fetch image blob from background script to bypass CORS
        fetch(request.imageUrl, {
            method: 'GET',
            mode: 'cors',
            credentials: 'omit'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.blob();
        })
        .then(blob => {
            // Convert blob to base64 for transmission
            const reader = new FileReader();
            reader.readAsDataURL(blob);
            reader.onloadend = function() {
                const base64Data = reader.result.split(',')[1]; // Remove data:image/...;base64, prefix
                sendResponse({ 
                    success: true, 
                    base64Data: base64Data,
                    mimeType: blob.type
                });
            };
        })
        .catch(error => {
            console.error('Error fetching image blob:', error);
            sendResponse({ 
                success: false, 
                error: error.message 
            });
        });
        return true; // Keep message channel open for async response
    }

    if (request.action === "annotate-image") {
        // Image annotation is now handled directly by the content script
        // This handler is kept for backward compatibility but does nothing
        console.log('Image annotation handled by content script');
        return false;
    }

    if (request.action === "translate-text") {
        console.log("Background script received translate-text request");
        getSettings().then(settings => {
            console.log("Translation settings:", settings);
            const url = buildEndpointUrl(settings.translateEndpoint, settings);
            
            // If no translation language is set, just return the original text
            if (!settings.targetLanguage || settings.targetLanguage === "none") {
                console.log("Translation disabled in settings");
                sendResponse({
                    success: true,
                    translatedText: request.text,
                    message: "Translation disabled in settings"
                });
                return;
            }
            
            const targetUrl = `${url}?target_language=${settings.targetLanguage}`;
            console.log("Sending translation request to:", targetUrl);
            // Add authentication header
            const headers = {
                "Content-Type": "application/json"
            };
            if (settings.accessCode) {
                headers["X-Auth-Code"] = settings.accessCode;
            }
            
            fetch(targetUrl, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ text: request.text })
            })
            .then(response => {
                console.log("Translation API response status:", response.status);
                return response.json();
            })
            .then(data => {
                console.log("Translation API response data:", data);
                sendResponse({ success: true, translatedText: data.translated_text });
            })
            .catch(error => {
                console.error('Error translating text:', error);
                sendResponse({ success: false, error: error.message });
            });
        });
        return true; // Keep message channel open for async response
    }
    
    // Handle settings request from content script
    if (request.action === "get-settings") {
        getSettings().then(settings => {
            sendResponse({ success: true, settings: settings });
        });
        return true;
    }
});

// Listen for settings changes from options page
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'settings-updated') {
        // Settings are automatically stored in chrome.storage.sync
        // Content scripts will receive the update via the message they sent
        console.log('Settings updated:', request.settings);
    }
});
