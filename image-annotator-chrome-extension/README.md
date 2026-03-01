# Image Annotator Chrome Extension

A Chrome extension that uses AI to annotate images with labels. Simply right-click on any image and select "Annotate Image" to see AI-generated labels overlaid on the image.

## Features

- **AI Image Annotation**: Right-click any image to annotate it with AI-generated labels
- **Visual Labels**: Labels are displayed directly on the image at the correct positions
- **Interactive**: Click on any label to remove all labels from that image
- **Text Translation**: Right-click selected text to translate it to your preferred language
- **Configurable Backend**: Set custom backend endpoint URL
- **Multi-Language Support**: Choose from 17 languages for translation
- **Responsive**: Works with images of any size
- **Quick Settings Access**: Click extension icon for quick status and settings

## Prerequisites

- Chrome browser (version 88 or higher)
- Running backend service (default: `http://localhost:8000`)
  - The backend endpoint is configurable in the extension settings

## Installation

1. **Download the extension files**
   - Clone or download this repository
   - Navigate to the `image-annotator-chrome-extension` folder

2. **Load the extension in Chrome**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (toggle in the top right)
   - Click "Load unpacked"
   - Select the `image-annotator-chrome-extension` folder

3. **Verify installation**
   - You should see "Image Annotator" in your extensions list
   - The extension icon should appear in your Chrome toolbar

## Usage

### Quick Access (Extension Icon)

1. Click the Image Annotator icon in your Chrome toolbar
2. View current backend endpoint and translation language
3. Test connection to your backend
4. Click "Open Full Settings" for detailed configuration

### Configure Settings

1. Click the extension icon
2. Click "⚙️ Open Full Settings" or right-click the extension icon and select "Options"
3. Configure the following settings:

#### Backend Configuration
- **Backend Endpoint URL**: The base URL of your AI backend service
  - Example: `http://localhost:8000` or `https://your-server.com`
  - Click preset buttons for common configurations
  - Click "Test Connection" to verify the backend is reachable

- **Translation Endpoint Path**: Path for text translation (default: `/translate`)
- **Image Annotation Endpoint Path**: Path for image annotation (default: `/image/annotate`)

#### Translation Settings
- **Target Language**: Choose from 17 languages:
  - English, Spanish, French, German, Italian, Portuguese
  - Russian, Japanese, Chinese, Korean, Arabic, Hindi
  - Dutch, Polish, Turkish, Vietnamese, Thai
  - Or select "No Translation" to disable translation

4. Click "💾 Save Settings" to apply changes

### Annotate Images

1. Browse to any webpage with images
2. Right-click on an image
3. Select "Annotate Image" from the context menu
4. Wait for the AI to process the image (loading indicator will show)
5. Labels will appear overlaid on the image (translated to your chosen language if enabled)
6. Click on any label to remove all labels from that image

### Translate Text

1. Select any text on a webpage
2. Right-click on the selection
3. Select "Translate Selection" from the context menu
4. The selected text will be replaced with its translation in your chosen language

## File Structure

```
image-annotator-chrome-extension/
├── manifest.json       # Extension configuration
├── background.js       # Background service worker (handles API calls & settings)
├── content.js          # Content script (runs on webpages)
├── options.html        # Settings page UI
├── options.js          # Settings page logic
├── popup.html          # Extension popup UI
├── popup.js            # Popup logic
├── icons/              # Extension icons
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── README.md           # This file
```

## How It Works

1. **Content Script** (`content.js`):
   - Runs on all HTTPS websites
   - Handles displaying labels on images
   - Listens for messages from the background script
   - Receives settings from background script

2. **Background Script** (`background.js`):
   - Creates context menu items on extension install
   - Handles context menu click events
   - Reads settings from Chrome storage
   - Builds API URLs based on configured endpoint
   - Communicates with the backend API
   - Forwards requests between content script and backend

3. **Options Page** (`options.html` + `options.js`):
   - Provides user interface for configuring settings
   - Stores settings in Chrome sync storage
   - Tests connection to backend
   - Broadcasts settings updates to all tabs

4. **Popup** (`popup.html` + `popup.js`):
   - Quick access to settings and status
   - Shows current configuration
   - Tests backend connection

5. **Backend API** (required):
   - Image annotation endpoint: `POST {backend_endpoint}/image/annotate`
   - Text translation endpoint: `POST {backend_endpoint}/translate?target_language={language}`
   - Health check endpoint: `GET {backend_endpoint}/health` (for connection testing)

## Permissions

The extension requires the following permissions:

- `activeTab`: To interact with the current webpage
- `contextMenus`: To create right-click menu items
- `storage`: To save and retrieve user settings
- `https://*/*`: To run on all HTTPS websites

Note: The backend endpoint is now configurable, so you can use any HTTP/HTTPS endpoint.

## Troubleshooting

### Labels not appearing

- Make sure the backend service is running at your configured endpoint
- Click the extension icon and click "Test Connection" to verify connectivity
- Check the browser console (F12) for error messages
- Verify that the image is fully loaded before right-clicking

### Context menu not showing

- Make sure the extension is enabled in `chrome://extensions/`
- Try reloading the webpage
- Check that you're on an HTTPS page (extension only works on HTTPS)

### Translation not working

- Open extension settings and verify the backend endpoint is correct
- Check that the target language is not set to "No Translation"
- Ensure the backend translation service is running
- Test the connection using the extension popup or settings page

### Cannot connect to backend

- Verify the backend endpoint URL in settings (include protocol: http:// or https://)
- Click "Test Connection" in the settings page to diagnose connection issues
- Check if your backend has a `/health` endpoint for connection testing
- If using localhost, ensure the backend is running and accessible
- For remote servers, verify SSL certificates are valid (for HTTPS)

### Settings not saving

- Check Chrome storage permissions
- Try resetting settings to defaults and reconfiguring
- Clear browser cache and reload the extension

## Development

### Modifying the extension

1. Edit the source files (`content.js`, `background.js`, `manifest.json`)
2. Go to `chrome://extensions/`
3. Click the refresh icon on the Image Annotator card
4. Reload the webpage to test changes

### Adding icons

Replace the placeholder icons in the `icons/` folder with your own:
- `icon16.png` - 16x16 pixels
- `icon48.png` - 48x48 pixels
- `icon128.png` - 128x128 pixels

## Known Limitations

- Requires a running backend service (configurable endpoint)
- Only works on HTTPS websites (Chrome extension security requirement)
- Image annotation may be slow for very large images
- Labels may not display correctly on images with unusual CSS positioning
- Backend must have a `/health` endpoint for connection testing (optional but recommended)

## License

MIT License - Feel free to modify and distribute

## Settings Reference

### Available Languages

| Language Code | Language Name |
|--------------|---------------|
| english | English |
| spanish | Spanish |
| french | French |
| german | German |
| italian | Italian |
| portuguese | Portuguese |
| russian | Russian |
| japanese | Japanese |
| chinese | Chinese |
| korean | Korean |
| arabic | Arabic |
| hindi | Hindi |
| dutch | Dutch |
| polish | Polish |
| turkish | Turkish |
| vietnamese | Vietnamese |
| thai | Thai |
| none | No Translation |

### Backend Endpoint Examples

- Local development: `http://localhost:8000`
- Local network: `http://192.168.1.100:8000`
- Remote server: `https://api.yourdomain.com`
- Custom port: `http://localhost:3000`

## Credits

Converted from Tampermonkey userscript to Chrome extension format.
