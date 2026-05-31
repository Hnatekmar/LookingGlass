import { build } from 'esbuild';
import * as fs from 'fs';
import * as path from 'path';

const isWatch = process.argv.includes('--watch');

const banner = `// ==UserScript==
// @name         Image Annotator
// @namespace    https://lookingglass
// @version      2.0
// @description  Annotate images using AI - Right-click on any image to annotate it with AI-generated labels. Configurable backend endpoint and translation language.
// @author       LookingGlass
// @match        http://*/*
// @match        https://*/*
// @grant        GM_xmlhttpRequest
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_registerMenuCommand
// @grant        GM_notification
// @connect      *
// @run-at       document-end
// ==/UserScript==
`;

async function buildScript() {
  try {
    const result = await build({
      entryPoints: ['src/main.ts'],
      bundle: true,
      outfile: 'dist/image-annotator.user.js',
      format: 'iife',
      target: 'es2020',
      minify: false,
      sourcemap: false,
      define: {
        'process.env.NODE_ENV': '"production"'
      },
      banner: {
        js: banner
      },
      write: false
    });

    // Ensure dist directory exists
    if (!fs.existsSync('dist')) {
      fs.mkdirSync('dist', { recursive: true });
    }

    // Write output
    fs.writeFileSync('dist/image-annotator.user.js', result.outputFiles[0].text);
    
    console.log('[build] Success!');
  } catch (error) {
    console.error('[build] Error:', error);
    throw error;
  }
}

if (isWatch) {
  // Simple watch implementation
  console.log('[build] Watching for changes...');
  fs.watch('src', { recursive: true }, async (eventType, filename) => {
    if (filename && filename.endsWith('.ts')) {
      console.log(`[build] Change detected: ${filename}`);
      try {
        await buildScript();
      } catch (err) {
        // Error already logged
      }
    }
  });
  
  // Initial build
  buildScript().then(() => {
    console.log('[build] Initial build complete!');
  });
} else {
  buildScript().then(() => {
    console.log('[build] Build complete!');
  }).catch(() => {
    process.exit(1);
  });
}
