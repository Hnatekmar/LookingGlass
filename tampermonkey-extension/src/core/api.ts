import type { AnnotationResponse, TranslationResponse } from '../types';
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
