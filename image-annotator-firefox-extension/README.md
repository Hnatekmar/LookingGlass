# Image Annotator - Tampermonkey Script

AI-powered image annotation and text translation for any webpage. Right-click on any image to annotate it with AI-generated labels, or select text to translate it.

> **Note:** This Tampermonkey script replaces the legacy Firefox extension. It provides better compatibility across all browsers (Firefox, Chrome, Edge, Safari) and requires no separate extension build process.

## Features

- 🏷️ **Image Annotation** - Right-click any image to detect and label text regions using AI
- 🌐 **Text Translation** - Select text and translate it to your preferred language  
- ⚙️ **Configurable Settings** - Customize backend endpoint, access code, and target language
- 💾 **Persistent Storage** - Settings are saved locally and persist across browser sessions
- 🎨 **Visual Overlays** - Labels are displayed with bounding boxes and hover tooltips
- 🔒 **Secure Authentication** - Uses access codes for backend authentication

## Prerequisites

1. **Tampermonkey Extension** installed in your browser:
   - [Firefox Add-on](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/)
   - [Chrome Web Store](https://chrome.google.com/webstore/detail/tampermonkey/)
   - [Edge Add-ons](https://microsoftedge.microsoft.com/addons/detail/tampermonkey/)
   - [Safari (via Mac App Store)](https://apps.apple.com/app/tampermonkey/id1496770082)

2. **Looking Glass Backend** running and accessible on your network

3. **Access Code** - Obtain from your Looking Glass instance after authentication

## Quick Start

### 1. Install Tampermonkey

Install the Tampermonkey browser extension from your browser's extension store (links above).

### 2. Install the Image Annotator Script

**Option A: Manual Install**

1. Navigate to your Tampermonkey Dashboard (click extension icon → Dashboard)
2. Click "+" to create a new script
3. Copy the entire contents of [`image-annotator-tampermonkey.user.js`](./image-annotator-tampermonkey.user.js)
4. Paste into the editor and save (`Ctrl+S` / `Cmd+S`)

**Option B: One-Click Install (if hosted)**

If your repository is hosted publicly, add these to the script metadata for auto-updates:
```javascript
// @downloadURL https://your-repo-url/raw/main/image-annotator-firefox-extension/image-annotator-tampermonkey.user.js
// @updateURL   https://your-repo-url/raw/main/image-annotator-firefox-extension/image-annotator-tampermonkey.user.js
```

### 3. Configure Backend Settings

1. Navigate to any webpage with images
2. Right-click anywhere on the page
3. Select **⚙️ Image Annotator Settings** from the context menu
4. Enter your settings:

   | Setting | Description | Example |
   |---------|-------------|---------|
   | Backend Endpoint | URL of your Looking Glass API | `http://192.168.122.1:9090/v1` |
   | Access Code | Authentication code from Looking Glass | `abc123xyz` |
   | Target Language | Language for translation | `english` |

5. Click OK on each prompt to save

## Usage

### Annotating Images

1. **Right-click** on any image on a webpage
2. Select **🏷️ Annotate Image** from the context menu
3. Wait for the annotation to complete (spinner notification appears)
4. View the results:
   - Text regions are highlighted with red bounding boxes
   - Hover over any box to see the full text in a tooltip
   - Click any box to dismiss the overlay

### Translating Text

1. **Select** any text on a webpage
2. **Right-click** on the selection
3. Select **🌐 Translate Text** from the context menu
4. The selected text will be replaced with the translation

### Changing Settings

1. Right-click anywhere on a webpage
2. Select **⚙️ Image Annotator Settings**
3. Enter new values when prompted (press Enter to keep current value)

## Network Configuration

### Local Development

If the backend is running on the same machine:
```
Backend Endpoint: http://localhost:8000/v1
```

### Remote/LAN Access

For accessing from other machines on your network, use NGINX as a reverse proxy:

```
Backend Endpoint: http://192.168.122.1:9090/v1
```

See [nginx/README.md](./nginx/README.md) for NGINX setup instructions.

### Why NGINX?

The Tampermonkey script uses `GM_xmlhttpRequest` which bypasses CORS restrictions, but using NGINX provides:
- ✅ Centralized SSL/TLS termination (if needed)
- ✅ Request logging and monitoring
- ✅ Rate limiting and security headers
- ✅ Load balancing for multiple backend instances
- ✅ Consistent endpoint URL regardless of backend changes

## Troubleshooting

### "Annotation failed" or "Network error"

1. **Verify backend is reachable:**
   ```bash
   curl http://192.168.122.1:9090/health
   ```
   Should return: `healthy`

2. **Check your settings:**
   - Right-click → Settings → Verify backend URL is correct
   - Ensure the URL includes `/v1` at the end

3. **Check access code:**
   - Verify the access code matches your backend configuration
   - A 401 error indicates authentication failure

### No labels appear on image

1. **Check browser console** (F12 → Console tab) for errors
2. **Verify the image loaded** - some images may be blocked by CSP
3. **Try a different image** - SVG or canvas-based images may not work

### Script not appearing in Tampermonkey

1. Ensure the script was saved (green checkmark in dashboard)
2. Check that `@match` patterns include the current site
3. Reload the webpage after installing the script

### Settings not saving

1. Check browser storage permissions
2. Try clearing Tampermonkey storage and re-entering settings
3. Ensure you're clicking OK on all prompts

## Supported Languages

The following languages are supported for translation:

**Europe:** English, French, German, Italian, Portuguese, Spanish, Dutch, Polish, Russian, Ukrainian, Turkish, Greek, Czech, Hungarian, Romanian, Swedish, Norwegian, Danish, Finnish, Bulgarian, Croatian, Slovak, Slovenian, Lithuanian, Latvian, Estonian

**Asia:** Japanese, Korean, Chinese (Simplified), Thai, Vietnamese, Indonesian, Malay, Tamil, Hindi, Bengali, Telugu, Marathi, Urdu, Arabic, Persian (Farsi), Hebrew, Burmese, Khmer, Lao

**Africa:** Swahili, Afrikaans, Amharic, Yoruba, Zulu

**Special:** None (No Translation)

## Files

```
image-annotator-firefox-extension/
├── image-annotator-tampermonkey.user.js  # Main Tampermonkey script
├── nginx/
│   ├── nginx.conf                        # NGINX reverse proxy config
│   ├── docker-compose.yml                # Docker Compose for NGINX
│   └── README.md                         # NGINX setup guide
└── README.md                             # This file
```

## Migration from Firefox Extension

If you were using the legacy Firefox extension:

1. **Uninstall the Firefox extension** from your browser
2. **Install Tampermonkey** (if not already installed)
3. **Install the Tampermonkey script** following the steps above
4. **Reconfigure your settings** (backend endpoint, access code, language)
5. **Test annotation** on a sample image

The Tampermonkey script provides the same functionality with better cross-browser support and easier maintenance.

## License

MIT License - See repository for details.

## Support

For issues or questions, please open an issue in the repository.
