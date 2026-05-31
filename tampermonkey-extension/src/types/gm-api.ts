/**
 * Tampermonkey GM_* API type definitions
 */
export interface GMXMLHttpRequestOptions {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';
  url: string;
  headers?: Record<string, string>;
  data?: string | FormData;
  responseType?: 'blob' | 'json' | 'text' | 'arraybuffer';
  timeout?: number;
  onload?: (response: GMXMLHttpRequestResponse) => void;
  onerror?: (error: { error: string }) => void;
  ontimeout?: () => void;
}

export interface GMXMLHttpRequestResponse {
  status: number;
  statusText: string;
  responseHeaders: string;
  response: any;
  responseText: string;
  finalUrl: string;
  readyState: number;
}

declare global {
  function GM_xmlhttpRequest(options: GMXMLHttpRequestOptions): void;
  function GM_setValue(key: string, value: any): void;
  function GM_getValue<T = any>(key: string, defaultValue?: T): T;
  function GM_registerMenuCommand(name: string, callback: () => void): void;
  function GM_notification(details: { title?: string; text: string; timeout?: number }): void;
}

export {};
