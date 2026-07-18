import { displayLabelsProgressive } from '../ui/annotation';
import { annotateImageStream } from '../core/api';
import { showNotification, showPersistentNotification, dismissPersistentNotification } from '../ui/notification';

let isAnnotating = false;

export function handleAnnotateImage(imageUrl: string, imgElement: HTMLImageElement): void {
  if (isAnnotating) {
    showNotification("Annotation in progress, please wait...", "warning");
    return;
  }

  isAnnotating = true;
  showPersistentNotification("Annotating image...");

  let labelCount = 0;

  annotateImageStream(imageUrl, {
    onLabels: (tile, labels) => {
      // Display labels progressively as they arrive
      labelCount += labels.length;
      displayLabelsProgressive(labels, imgElement, tile === 0);
    },
    onTranslate: (updates) => {
      // Translations arrive as a batch — update the displayed text
      showNotification(`Translations applied to ${updates.length} label(s)`, "info");
    },
    onError: (detail) => {
      dismissPersistentNotification();
      isAnnotating = false;
      showNotification(`Annotation error: ${detail}`, "error");
    },
    onComplete: () => {
      dismissPersistentNotification();
      isAnnotating = false;
      if (labelCount > 0) {
        showNotification(`Found ${labelCount} text region(s)`, "success");
      } else {
        showNotification("No text found in image", "info");
      }
    },
    onProgress: (_progress) => {
      // Progress updates — could be used for a progress bar in the future
    },
  }).catch((err) => {
    console.error("[Image Annotator] Annotation error:", err);
    dismissPersistentNotification();
    isAnnotating = false;
    showNotification(err.message || "Annotation failed", "error");
  });
}

export function isAnnotationInProgress(): boolean {
  return isAnnotating;
}
