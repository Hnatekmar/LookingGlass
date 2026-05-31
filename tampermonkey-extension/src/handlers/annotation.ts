import { displayLabelsOnImage } from '../ui/annotation';
import { annotateImage as apiAnnotateImage } from '../core/api';
import { showNotification, showPersistentNotification, dismissPersistentNotification } from '../ui/notification';

let isAnnotating = false;

export function handleAnnotateImage(imageUrl: string, imgElement: HTMLImageElement): void {
  if (isAnnotating) {
    showNotification("Annotation in progress, please wait...", "warning");
    return;
  }

  isAnnotating = true;
  const dismissNotification = showPersistentNotification("Annotating image...");

  let progress = 0;
  const updateProgress = (newProgress: number) => {
    progress = newProgress;
    // Could update notification with progress here if desired
  };

  apiAnnotateImage(imageUrl, updateProgress)
    .then((response) => {
      dismissPersistentNotification();
      isAnnotating = false;

      if (response.success) {
        if (response.labels && response.labels.length > 0) {
          displayLabelsOnImage(response.labels, imgElement);
          showNotification(`Found ${response.labels.length} text region(s)`, "success");
        } else {
          showNotification("No text found in image", "info");
        }
      } else {
        showNotification(response.error || "Annotation failed", "error");
      }
    })
    .catch((err) => {
      console.error("[Image Annotator] Annotation error:", err);
      dismissPersistentNotification();
      isAnnotating = false;
      showNotification(err.message || "Annotation failed", "error");
    });
}

export function isAnnotationInProgress(): boolean {
  return isAnnotating;
}
