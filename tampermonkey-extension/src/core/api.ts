import type { AnnotationResponse, Label, TranslationResponse } from '../types';
import { getSettings } from '../core/settings';

export async function fetchImageBlob(imageUrl: string): Promise<Blob> {
  return new Promise((resolve, reject) => {
    GM_xmlhttpRequest({
      method: "GET",
      url: imageUrl,
      responseType: "blob",
      timeout: 60000,
      onload: (response) => {
        if (response.status >= 400) {
          reject(new Error(`Failed to fetch image (${response.status})`));
          return;
        }
        resolve(response.response as Blob);
      },
      onerror: (err) => reject(new Error(`Image fetch error: ${err.error || "Unknown error"}`)),
      ontimeout: () => reject(new Error("Image fetch timed out"))
    });
  });
}

export async function resizeImageBlob(blob: Blob, maxDim: number): Promise<Blob> {
  const img = await createImageBitmap(blob);
  const width = img.width;
  const height = img.height;

  if (width <= maxDim && height <= maxDim) {
    return blob;
  }

  let newWidth: number, newHeight: number;
  if (width > height) {
    newHeight = (height / width) * maxDim;
    newWidth = maxDim;
  } else {
    newWidth = (width / height) * maxDim;
    newHeight = maxDim;
  }

  const canvas = document.createElement("canvas");
  canvas.width = newWidth;
  canvas.height = newHeight;
  const ctx = canvas.getContext("2d");
  if (!ctx) return blob;
  
  ctx.drawImage(img, 0, 0, newWidth, newHeight);

  return new Promise((resolve) => {
    canvas.toBlob((resizedBlob) => {
      resolve(resizedBlob || blob);
    }, "image/png");
  });
}

/** SSE event types for the streaming annotation endpoint */
export interface SSETranslateUpdate {
  index: number;
  text: string;
}

type SSEEventCallback = {
  onLabels?: (tile: number, labels: Label[]) => void;
  onTranslate?: (updates: SSETranslateUpdate[]) => void;
  onError?: (detail: string) => void;
  onComplete?: () => void;
};

/**
 * Parse SSE text and invoke callbacks for each event found.
 */
function parseSSEBuffer(buffer: string, callbacks: SSEEventCallback): string {
  // Split on double newline (SSE event boundary)
  const parts = buffer.split('\n\n');
  // The last part may be incomplete — keep it in the buffer
  const complete = parts.slice(0, -1);
  const remainder = parts[parts.length - 1];

  for (const block of complete) {
    const lines = block.trim().split('\n');
    let eventType = '';
    let dataStr = '';

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim();
      } else if (line.startsWith('data: ')) {
        dataStr = line.slice(6).trim();
      }
    }

    if (!eventType || !dataStr) continue;

    try {
      const data = JSON.parse(dataStr);
      switch (eventType) {
        case 'labels':
          callbacks.onLabels?.(data.tile, data.labels);
          break;
        case 'translate':
          callbacks.onTranslate?.(data.updates);
          break;
        case 'error':
          callbacks.onError?.(data.detail || 'Unknown error');
          break;
        case 'complete':
          callbacks.onComplete?.();
          break;
      }
    } catch {
      // Skip unparseable events
    }
  }

  return remainder;
}

export async function annotateImage(imageUrl: string, onProgress?: (progress: number) => void): Promise<AnnotationResponse> {
  const settings = getSettings();
  const endpoint = settings.backendEndpoint;
  const authCode = settings.accessCode;
  const targetLang = settings.targetLanguage;
  const qualityMode = settings.qualityMode || "balanced";

  try {
    onProgress?.(10);
    const blob = await fetchImageBlob(imageUrl);
    onProgress?.(70);
    // Don't resize client-side - let backend handle tiling decisions based on quality mode
    // const resizedBlob = await resizeImageBlob(blob, 1000);

    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append("data", blob);

      const xhrUrl = `${endpoint}/image/annotate?translate=true&translate_language=${encodeURIComponent(targetLang)}&quality_mode=${encodeURIComponent(qualityMode)}`;

      GM_xmlhttpRequest({
        method: "POST",
        url: xhrUrl,
        headers: { "X-Auth-Code": authCode },
        data: formData,
        timeout: 600000,
        onload: (response) => {
          onProgress?.(100);
          if (response.status === 401) {
            reject(new Error("Authentication failed. Please check your access code in settings."));
            return;
          }
          if (response.status >= 400) {
            reject(new Error(`Annotation failed (${response.status})`));
            return;
          }
          try {
            const data = JSON.parse(response.responseText);
            resolve({ success: true, labels: data.labels || [] });
          } catch (err) {
            reject(new Error("Invalid response from server"));
          }
        },
        onerror: (err) => reject(new Error(`Network error: ${err.error || "Unknown error"}`)),
        ontimeout: () => reject(new Error("Annotation request timed out"))
      });
    });
  } catch (error) {
    onProgress?.(0);
    throw error;
  }
}

/**
 * Annotate an image using the SSE streaming endpoint.
 * Labels are delivered progressively via onLabels as tiles are processed.
 *
 * Returns the final merged AnnotationResponse after all tiles complete.
 */
export async function annotateImageStream(
  imageUrl: string,
  callbacks: SSEEventCallback & { onProgress?: (progress: number) => void },
): Promise<AnnotationResponse> {
  const settings = getSettings();
  const endpoint = settings.backendEndpoint;
  const authCode = settings.accessCode;
  const targetLang = settings.targetLanguage;
  const qualityMode = settings.qualityMode || "balanced";

  try {
    callbacks.onProgress?.(10);
    const blob = await fetchImageBlob(imageUrl);
    callbacks.onProgress?.(30);

    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append("data", blob);

      const xhrUrl = `${endpoint}/image/annotate/stream?translate=true&translate_language=${encodeURIComponent(targetLang)}&quality_mode=${encodeURIComponent(qualityMode)}`;

      let buffer = '';
      const allLabels: Label[] = [];

      GM_xmlhttpRequest({
        method: "POST",
        url: xhrUrl,
        headers: { "X-Auth-Code": authCode },
        data: formData,
        timeout: 600000,
        // Use text response type to get progressive chunks via onprogress
        responseType: "text",

        onprogress: (response) => {
          if (response.responseText) {
            const newData = response.responseText;
            // If we get the full accumulated text, diff against our buffer
            const newChunk = newData.length > buffer.length
              ? newData.slice(buffer.length)
              : newData;

            // Check for the streaming chunks — GM_xmlhttpRequest may give us
            // the full text in onload, so onprogress may not fire incrementally.
            // We still handle it here for progressive rendering.
            if (newChunk) {
              buffer = newData;
              buffer = parseSSEBuffer(buffer, {
                onLabels: (tile, labels) => {
                  allLabels.push(...labels);
                  callbacks.onLabels?.(tile, labels);
                  callbacks.onProgress?.(50 + Math.min(tile * 5, 40));
                },
                onTranslate: (updates) => callbacks.onTranslate?.(updates),
                onError: (detail) => callbacks.onError?.(detail),
                onComplete: () => {},
              });
            }
          }
        },

        onload: (response) => {
          if (response.status === 401) {
            reject(new Error("Authentication failed. Please check your access code in settings."));
            return;
          }
          if (response.status >= 400) {
            reject(new Error(`Annotation failed (${response.status})`));
            return;
          }

          // Parse any remaining data in the buffer
          if (response.responseText) {
            buffer = response.responseText;
          }

          let hadComplete = false;
          parseSSEBuffer(buffer, {
            onLabels: (tile, labels) => {
              allLabels.push(...labels);
              callbacks.onLabels?.(tile, labels);
            },
            onTranslate: (updates) => callbacks.onTranslate?.(updates),
            onError: (detail) => {
              callbacks.onError?.(detail);
              reject(new Error(detail));
            },
            onComplete: () => {
              hadComplete = true;
              callbacks.onComplete?.();
            },
          });

          if (!hadComplete) {
            // No complete event found — assume response is the full JSON
            try {
              const data = JSON.parse(response.responseText);
              if (data.labels) {
                allLabels.push(...data.labels);
              }
              resolve({ success: true, labels: allLabels });
              return;
            } catch {
              // Not JSON — just resolve with what we have
            }
          }

          callbacks.onProgress?.(100);
          resolve({ success: true, labels: allLabels });
        },

        onerror: (err) => reject(new Error(`Network error: ${err.error || "Unknown error"}`)),
        ontimeout: () => reject(new Error("Annotation request timed out")),
      });
    });
  } catch (error) {
    callbacks.onProgress?.(0);
    throw error;
  }
}

export async function translateText(text: string): Promise<TranslationResponse> {
  const settings = getSettings();
  const endpoint = settings.backendEndpoint;
  const authCode = settings.accessCode;
  const targetLang = settings.targetLanguage;

  return new Promise((resolve, reject) => {
    GM_xmlhttpRequest({
      method: "POST",
      url: `${endpoint}/translate?target_language=${encodeURIComponent(targetLang)}`,
      headers: {
        "Content-Type": "application/json",
        "X-Auth-Code": authCode
      },
      data: JSON.stringify({ text: text }),
      timeout: 300000,
      onload: (response) => {
        if (response.status === 401) {
          resolve({ success: false, error: "Authentication failed. Please check your access code." });
          return;
        }
        if (response.status >= 400) {
          resolve({ success: false, error: `Translation failed (${response.status})` });
          return;
        }
        try {
          const data = JSON.parse(response.responseText);
          resolve({ success: true, translatedText: data.translated_text || data.translation });
        } catch (err) {
          reject(new Error("Invalid response from server"));
        }
      },
      onerror: (err) => reject(new Error(`Network error: ${err.error || "Unknown error"}`)),
      ontimeout: () => reject(new Error("Translation request timed out"))
    });
  });
}

export async function testConnection(): Promise<{ success: boolean; error?: string }> {
  const settings = getSettings();

  return new Promise((resolve) => {
    GM_xmlhttpRequest({
      method: "GET",
      url: `${settings.backendEndpoint}/health`,
      timeout: 10000,
      onload: (res) => {
        if (res.status === 200) {
          resolve({ success: true });
        } else {
          resolve({ success: false, error: `Status ${res.status}` });
        }
      },
      onerror: () => resolve({ success: false, error: "Network error" }),
      ontimeout: () => resolve({ success: false, error: "Timeout" })
    });
  });
}
