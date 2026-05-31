/**
 * Application types and interfaces
 */

export interface Settings {
  backendEndpoint: string;
  accessCode: string;
  targetLanguage: string;
  autoAnnotate: boolean;
  qualityMode: 'fast' | 'balanced' | 'accurate';
}

export interface Label {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  text: string;
}

export interface AnnotationResponse {
  success: boolean;
  labels?: Label[];
  error?: string;
}

export interface TranslationResponse {
  success: boolean;
  translatedText?: string;
  error?: string;
}

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface ContextMenuState {
  target: EventTarget | null;
  mode: 'image' | 'text' | null;
  selectedText: string | null;
}
