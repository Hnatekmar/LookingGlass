# Image Annotator - Firefox Extension

A Firefox WebExtension that performs AI-powered image annotation and text translation using the Looking Glass backend.

## Features

- **Right-click Image Annotation**: Right-click any image and select "Annotate Image" to get AI-powered text detection and labeling
- **Text Translation**: Select text and right-click to translate via the Looking Glass LLM backend
- **Configurable Backend**: Set your Looking Glass server URL and authentication code
- **Multi-language Support**: Translate to 20+ languages
- **Persistent Settings**: All settings saved to browser storage and persist across sessions

## Installation (Development)

1. Open Firefox
2. Navigate to `about:debugging#/runtime/this-firefox`
3. Click "Load Temporary Add-on..."
4. Select the `manifest.json` file from this directory

## Configuration

1. Click the extension icon in the toolbar
2. Click "Open Settings"
3. Enter your Looking Glass backend URL (e.g., `http://localhost:8000`)
4. Enter your access code (if required)
5. Set your default translation language
6. Click "Test Connection" to verify the backend is reachable
7. Click "Save Settings"

## Usage

### Annotate Images
1. Navigate to any webpage with images
2. Right-click on an image
3. Select "Annotate Image"
4. The extension will send the image to the backend and display labeled regions

### Translate Text
1. Select text on any webpage
2. Right-click and select "Translate Text"
3. The selected text will be replaced with the translated version

## Files

- `manifest.json` - Firefox WebExtension manifest (Manifest V3)
- `background.js` - Background script (persistent page) handling context menus and API communication
- `content.js` - Content script injected into pages for image overlay and DOM manipulation
- `options.html` / `options.js` - Options page for configuration
- `popup.html` / `popup.js` - Popup UI for quick status and settings access
- `icons/` - Extension icons (16x16, 48x48, 128x128)

## Backend Requirements

The extension communicates with a Looking Glass backend exposing these endpoints:

- `POST /image/annotate` - Image annotation with OCR
  - Multipart form data with `data` field containing the image
  - Query params: `translate`, `translate_language`
  - Headers: `X-Auth-Code`
  - Response: `{ labels: [{ x1, y1, x2, y2, text }] }`

- `POST /translate` - Text translation
  - JSON body: `{ text }`
  - Query params: `target_language`
  - Headers: `X-Auth-Code`
  - Response: `{ translated_text }`

## Firefox-Specific Notes

This extension uses Firefox's persistent background page model (not service workers) for full compatibility with Firefox's WebExtension implementation.

## License

Same as the Looking Glass project.