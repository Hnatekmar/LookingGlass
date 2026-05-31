# Image Annotator Tampermonkey

AI-powered image annotation and text translation userscript, built with TypeScript.

## Features

- 🏷️ **Image Annotation** - Right-click any image to annotate with AI-generated labels
- 🌐 **Text Translation** - Right-click selected text to translate
- ⚙️ **Configurable Settings** - Backend endpoint, access code, target language
- 🎨 **Modern UI** - Clean, professional interface with smooth animations
- 🌙 **Dark Mode Ready** - Styles that work well in both light and dark contexts
- ⌨️ **Keyboard Shortcuts** - Press Escape to close modals and context menus

## Project Structure

```
src/
├── types/           # TypeScript type definitions
│   ├── gm-api.ts    # Tampermonkey GM_* API types
│   └── index.ts     # Application types
├── core/            # Core business logic
│   ├── settings.ts  # Settings management
│   └── api.ts       # Backend API calls
├── ui/              # UI components
│   ├── modal.ts     # Modal dialog component
│   ├── notification.ts  # Toast notifications
│   ├── settings.ts  # Settings dialog
│   ├── context-menu.ts  # Right-click menu
│   ├── annotation.ts  # Label overlay display
│   ├── translation.ts  # Translation popup
│   └── styles.ts    # Base CSS injection
├── handlers/        # Event handlers
│   ├── annotation.ts  # Image annotation handler
│   ├── translation.ts  # Text translation handler
│   └── index.ts     # Handler exports
└── main.ts          # Entry point
```

## Development

### Prerequisites

- Node.js 18+
- npm

### Setup

```bash
npm install
```

### Build

```bash
npm run build
```

Output: `dist/image-annotator.user.js`

### Watch Mode (auto-rebuild on changes)

```bash
npm run watch
```

## Installation

1. Install [Tampermonkey](https://www.tampermonkey.net/) browser extension
2. Build the project: `npm run build`
3. Open Tampermonkey dashboard
4. Click "Create a new script"
5. Copy contents of `dist/image-annotator.user.js`
6. Save (Ctrl+S)

## Usage

### Image Annotation
1. Right-click on any image
2. Select "Annotate Image"
3. Wait for AI processing
4. View labels overlaid on the image
5. Click any label to dismiss

### Text Translation
1. Select text on the page
2. Right-click the selection
3. Select "Translate Selection"
4. View translation in popup

### Settings
- Access via Tampermonkey menu → "⚙️ Image Annotator Settings"
- Or right-click → Settings

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Backend Endpoint | `http://localhost:8000/v1` | Your AI backend API URL |
| Access Code | (empty) | Authentication code for backend |
| Target Language | `english` | Language for translations |
| Auto-annotate | `false` | (Reserved for future use) |

## Improvements (v2.0 TypeScript)

- ✅ Better modal positioning on scrollable pages
- ✅ Loading progress indicators
- ✅ Real-time URL validation in settings
- ✅ Dark mode compatible styling
- ✅ Full TypeScript type safety
- ✅ Modular, maintainable codebase
- ✅ Escape key to close modals/menus

## License

MIT
