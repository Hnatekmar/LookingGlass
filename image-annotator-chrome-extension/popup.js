// Popup script for Image Annotator Chrome Extension

const DEFAULT_SETTINGS = {
    backendEndpoint: 'http://localhost:8000',
    translateEndpoint: '/translate',
    annotateEndpoint: '/image/annotate',
    targetLanguage: 'english'
};

// Load and display current settings
function loadSettings() {
    chrome.storage.sync.get(DEFAULT_SETTINGS, (settings) => {
        document.getElementById('endpointDisplay').innerHTML = 
            `<strong>Endpoint:</strong> ${settings.backendEndpoint}`;
        
        const languageNames = {
            'english': 'English',
            'spanish': 'Spanish',
            'french': 'French',
            'german': 'German',
            'italian': 'Italian',
            'portuguese': 'Portuguese',
            'russian': 'Russian',
            'japanese': 'Japanese',
            'chinese': 'Chinese',
            'korean': 'Korean',
            'arabic': 'Arabic',
            'hindi': 'Hindi',
            'dutch': 'Dutch',
            'polish': 'Polish',
            'turkish': 'Turkish',
            'vietnamese': 'Vietnamese',
            'thai': 'Thai',
            'none': 'Disabled'
        };
        
        const languageName = languageNames[settings.targetLanguage] || settings.targetLanguage;
        document.getElementById('languageDisplay').innerHTML = 
            `<strong>Translation:</strong> ${languageName}`;
        
        document.getElementById('currentSettings').style.display = 'block';
        
        // Test connection
        testConnection(settings.backendEndpoint);
    });
}

// Test connection to backend
function testConnection(endpoint) {
    const statusEl = document.getElementById('status');
    statusEl.className = 'status';
    statusEl.textContent = 'Testing connection...';
    
    fetch(`${endpoint}/health`)
        .then(response => {
            if (response.ok) {
                statusEl.className = 'status connected';
                statusEl.textContent = '✓ Backend connected successfully!';
            } else {
                statusEl.className = 'status disconnected';
                statusEl.textContent = '⚠ Backend responded with status: ' + response.status;
            }
        })
        .catch(error => {
            statusEl.className = 'status disconnected';
            statusEl.textContent = '✗ Cannot connect to backend';
        });
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    
    document.getElementById('testConnection').addEventListener('click', () => {
        chrome.storage.sync.get(DEFAULT_SETTINGS, (settings) => {
            testConnection(settings.backendEndpoint);
        });
    });
    
    document.getElementById('openSettings').addEventListener('click', (e) => {
        e.preventDefault();
        chrome.runtime.openOptionsPage();
        window.close();
    });
});
