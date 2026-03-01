// Content script for Image Annotator Chrome Extension

(function() {
    'use strict';

    // Helper function to generate/retrieve unique image identifier
    function getImageId(imageElement) {
        if (!imageElement.dataset.labelImageId) {
            imageElement.dataset.labelImageId = `img-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        }
        return imageElement.dataset.labelImageId;
    }

    const LABEL_COORDINATE_MAX = 1000; // Normalization constant

    function displayLabelsOnImage(labels, imageElement) {
        // Validate inputs
        if (!imageElement || !imageElement.parentNode) {
            console.warn("Invalid image element or no parent node");
            return;
        }
        if (!labels || labels.length === 0) {
            return;
        }

        try {
            // Remove ONLY existing containers for THIS specific image
            const existingContainer = imageElement.parentNode.querySelector(
                '.image-label-container[data-image-id]'
            );
            if (existingContainer && existingContainer.dataset.imageId === getImageId(imageElement)) {
                existingContainer.remove();
            }

            // Ensure image parent has relative positioning for absolute child (label container)
            const parent = imageElement.parentNode;
            const computedStyle = window.getComputedStyle(parent);
            const originalPosition = computedStyle.position;
            
            // Only set position if it's static (the default)
            if (originalPosition === 'static') {
                parent.style.position = 'relative';
            }

            // Get actual rendered dimensions
            const width = imageElement.offsetWidth;
            const height = imageElement.offsetHeight;

            if (width === 0 || height === 0) {
                console.warn("Image has zero dimensions");
                return;
            }

            // Get the image's position relative to its parent
            const topOffset = imageElement.offsetTop;
            const leftOffset = imageElement.offsetLeft;

            // Create container positioned to overlay the image
            const labelContainer = document.createElement('div');
            labelContainer.className = 'image-label-container';
            labelContainer.dataset.imageId = getImageId(imageElement);
            
            // Position the container to exactly overlay the image
            labelContainer.style.cssText = `
                position: absolute;
                top: ${topOffset}px;
                left: ${leftOffset}px;
                width: ${width}px;
                height: ${height}px;
                pointer-events: none;
                z-index: 10001;
                overflow: visible;
            `;

            // Add labels
            labels.forEach(label => {
                // Enhanced validation
                if (!label ||
                    typeof label.x1 !== 'number' ||
                    typeof label.y1 !== 'number' ||
                    typeof label.x2 !== 'number' ||
                    typeof label.y2 !== 'number' ||
                    !label.text) {
                    return;
                }
                // Validate coordinate bounds (normalized 0-1)
                if (label.x1 < 0 || label.x1 > 1 ||
                    label.x2 < 0 || label.x2 > 1 ||
                    label.y1 < 0 || label.y1 > 1 ||
                    label.y2 < 0 || label.y2 > 1) {
                    console.warn("Label coordinates out of bounds (normalized):", label);
                    return;
                }

                // Rescale normalized coordinates to percentage values (0-1 becomes 0%-100%)
                const x1 = label.x1 * 100;
                const y1 = label.y1 * 100;
                const x2 = label.x2 * 100;
                const y2 = label.y2 * 100;

                const labelWidth = x2 - x1;
                const labelHeight = y2 - y1;

                // Calculate position and dimensions using percentage coordinates
                const left = x1;
                const top = y1;
                const labelElement = document.createElement('div');
                labelElement.className = 'image-label';
                labelElement.textContent = label.text;
                labelElement.title = label.text; // Tooltip for truncated text

                // Add click event listener to remove labels on left click
                labelElement.addEventListener('click', function(e) {
                    e.stopPropagation();
                    // Remove the entire label container
                    if (labelContainer.parentNode) {
                        labelContainer.remove();
                    }
                });

                // Determine if label should be vertical based on aspect ratio
                const isVertical = labelHeight > labelWidth;

                let styles = `
                    position: absolute;
                    left: ${left}%;
                    top: ${top}%;
                    width: ${labelWidth}%;
                    height: ${labelHeight}%;
                    background-color: rgba(0, 0, 0, 0.7);
                    color: white;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-family: Arial, sans-serif;
                    pointer-events: auto;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-sizing: border-box;
                `;

                if (isVertical) {
                    // Apply vertical text styles
                    styles += `
                        writing-mode: vertical-rl;
                        text-orientation: upright;
                        overflow: hidden;
                    `;
                } else {
                    styles += `
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    `;
                }

                labelElement.style.cssText = styles;
                labelContainer.appendChild(labelElement);
            });

            // Insert the container as a sibling after the image element
            // Position it absolutely over the image
            if (imageElement.nextSibling) {
                imageElement.parentNode.insertBefore(labelContainer, imageElement.nextSibling);
            } else {
                imageElement.parentNode.appendChild(labelContainer);
            }

        } catch (error) {
            console.error("Error displaying labels:", error);
        }
    }

    // Function to show results in a popup
    function showResults(results, imageDimensions = null) {
        // Create a simple popup to display results
        const popup = document.createElement('div');
        popup.className = 'annotation-popup';

        popup.innerHTML = '<h3>Image Annotations</h3>';

        if (results.labels && results.labels.length > 0) {
            results.labels.forEach(label => {
                const labelDiv = document.createElement('div');
                labelDiv.className = 'annotation-label';
                labelDiv.textContent = label.text;
                popup.appendChild(labelDiv);
            });
        } else {
            popup.innerHTML += '<p>No labels found</p>';
        }

        document.body.appendChild(popup);

        // Remove popup after 10 seconds
        setTimeout(() => {
            if (popup.parentNode) {
                popup.parentNode.removeChild(popup);
            }
        }, 10000);
    }

    // Function to translate selected text
    function translateText(text, settings = null) {
        const loadingIndicator = document.createElement('div');
        loadingIndicator.textContent = 'Translating...';
        loadingIndicator.style.position = 'fixed';
        loadingIndicator.style.top = '10px';
        loadingIndicator.style.right = '10px';
        loadingIndicator.style.background = 'black';
        loadingIndicator.style.border = '1px solid #ccc';
        loadingIndicator.style.padding = '15px';
        loadingIndicator.style.borderRadius = '5px';
        loadingIndicator.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        loadingIndicator.style.zIndex = '10001';
        loadingIndicator.style.fontFamily = 'Arial, sans-serif';
        loadingIndicator.style.display = 'flex';
        loadingIndicator.style.alignItems = 'center';
        loadingIndicator.style.gap = '8px';
        document.body.appendChild(loadingIndicator);

        const spinner = document.createElement('div');
        spinner.style.border = '2px solid #f3f3f3';
        spinner.style.borderTop = '2px solid #3498db';
        spinner.style.borderRadius = '50%';
        spinner.style.width = '16px';
        spinner.style.height = '16px';
        spinner.style.animation = 'spin 1s linear infinite';
        loadingIndicator.appendChild(spinner);

        // Send message to background script for translation
        chrome.runtime.sendMessage({
            action: "translate-text",
            text: text,
            settings: settings
        }, function(response) {
            if (loadingIndicator.parentNode) {
                loadingIndicator.parentNode.removeChild(loadingIndicator);
            }

            if (response && response.success && response.translatedText) {
                // Try to find and replace the selected text
                const selection = window.getSelection();
                if (selection.rangeCount > 0) {
                    const range = selection.getRangeAt(0);
                    const span = document.createElement('span');
                    span.textContent = response.translatedText;
                    range.deleteContents();
                    range.insertNode(span);
                }
            } else if (response && !response.success) {
                console.error('Translation error:', response.error);
                alert('Translation failed: ' + response.error);
            }
        });
    }

    // Function to annotate an image
    function annotateImage(imageUrl, imageElement, settings = null) {
        // Show loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.textContent = 'Processing...';
        loadingIndicator.style.position = 'fixed';
        loadingIndicator.style.top = '10px';
        loadingIndicator.style.right = '10px';
        loadingIndicator.style.background = 'black';
        loadingIndicator.style.border = '1px solid #ccc';
        loadingIndicator.style.padding = '15px';
        loadingIndicator.style.borderRadius = '5px';
        loadingIndicator.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        loadingIndicator.style.zIndex = '10001';
        loadingIndicator.style.fontFamily = 'Arial, sans-serif';
        loadingIndicator.style.display = 'flex';
        loadingIndicator.style.alignItems = 'center';
        loadingIndicator.style.gap = '8px';
        document.body.appendChild(loadingIndicator);

        // Add spinner animation
        const spinner = document.createElement('div');
        spinner.style.border = '2px solid #f3f3f3';
        spinner.style.borderTop = '2px solid #3498db';
        spinner.style.borderRadius = '50%';
        spinner.style.width = '16px';
        spinner.style.height = '16px';
        spinner.style.animation = 'spin 1s linear infinite';
        loadingIndicator.appendChild(spinner);

        // Add CSS for spinner animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);

        // Fetch the image blob through background script to bypass CORS
        chrome.runtime.sendMessage(
            { action: "fetch-image-blob", imageUrl: imageUrl },
            function(response) {
                if (!response || !response.success) {
                    const errorMsg = response?.error || 'Unknown error';
                    console.error('Error fetching image blob:', errorMsg);
                    if (loadingIndicator.parentNode) {
                        loadingIndicator.parentNode.removeChild(loadingIndicator);
                    }
                    alert('Failed to fetch image: ' + errorMsg);
                    return;
                }

                // Convert base64 back to blob
                const byteCharacters = atob(response.base64Data);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: response.mimeType });

                // Create an image from the blob
                const img = new Image();
                const objectUrl = URL.createObjectURL(blob);

                img.onload = function() {
                    // Clean up the object URL
                    URL.revokeObjectURL(objectUrl);

                    // Create canvas to resize image if needed
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');

                    // Set max dimensions (similar to backend)
                    const maxWidth = 1000;
                    const maxHeight = 1000;

                    let width = this.width;
                    let height = this.height;

                    // Calculate new dimensions while maintaining aspect ratio
                    if (width > maxWidth || height > maxHeight) {
                        const ratio = Math.min(maxWidth / width, maxHeight / height);
                        width = width * ratio;
                        height = height * ratio;
                    }

                    canvas.width = width;
                    canvas.height = height;

                    // Draw image on canvas
                    ctx.drawImage(this, 0, 0, width, height);

                    // Convert to blob
                    canvas.toBlob(function(resizedBlob) {
                        // Create FormData and send directly to backend
                        const formData = new FormData();
                        formData.append('data', resizedBlob, 'image.jpg');
                        
                        // Build the endpoint URL
                        let url = settings.backendEndpoint.replace(/\/$/, '') + 
                                  (settings.annotateEndpoint.startsWith('/') ? 
                                   settings.annotateEndpoint : '/' + settings.annotateEndpoint);
                        
                        // Add translate parameters if translation is enabled
                        if (settings.targetLanguage && settings.targetLanguage !== 'none') {
                            url += `?translate=true&translate_language=${settings.targetLanguage}`;
                        }
                        
                        // Send directly to backend
                        fetch(url, {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(result => {
                            // Remove loading indicator
                            if (loadingIndicator.parentNode) {
                                loadingIndicator.parentNode.removeChild(loadingIndicator);
                            }
                            
                            console.log('Annotation result:', result);
                            showResults(result);
                            console.log("Displaying labels on image");
                            
                            // Display labels directly on image
                            console.log("Original image element:", imageElement);
                            displayLabelsOnImage(result.labels, imageElement);
                        })
                        .catch(error => {
                            // Remove loading indicator
                            if (loadingIndicator.parentNode) {
                                loadingIndicator.parentNode.removeChild(loadingIndicator);
                            }
                            
                            console.error('Annotation error:', error);
                            alert('Image annotation failed: ' + error.message);
                        });
                    }, 'image/jpeg', 0.9);
                };

                img.onerror = function() {
                    console.error('Error loading image from blob');
                    URL.revokeObjectURL(objectUrl);
                    if (loadingIndicator.parentNode) {
                        loadingIndicator.parentNode.removeChild(loadingIndicator);
                    }
                };

                img.src = objectUrl;
            }
        );
    }

    console.log("Image Annotator content script loaded");

    // Listen for settings updates from background script
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === "settings-updated") {
            console.log("Settings updated in content script:", request.settings);
            // Settings are now available for future operations
        }
        return true;
    });

    // Add styles for popup and labels
    const style = document.createElement('style');
    style.textContent = `
        .annotation-popup {
            position: fixed;
            top: 10px;
            right: 10px;
            background: black;
            border: 1px solid #ccc;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 10000;
            max-width: 300px;
            font-family: Arial, sans-serif;
        }
        .annotation-popup h3 {
            margin: 0 0 10px 0;
            color: white;
            font-size: 16px;
        }
        .annotation-label {
            margin: 5px 0;
            padding: 5px;
            border-bottom: 1px solid #eee;
            color: white;
        }
        .image-label {
            position: absolute;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-family: Arial, sans-serif;
            white-space: nowrap;
            pointer-events: none;
        }
        .image-label-container {
            pointer-events: none;
            z-index: 10001 !important;
            position: absolute;
        }
        .image-label-container .image-label {
            pointer-events: auto;
        }
    `;
    document.head.appendChild(style);

    // Listen for messages from background script
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === "annotate-image" && request.imageUrl) {
            // Find the image element by src
            const images = document.querySelectorAll('img');
            let targetImage = null;
            
            for (let img of images) {
                if (img.src === request.imageUrl || img.getAttribute('src') === request.imageUrl) {
                    targetImage = img;
                    break;
                }
            }
            
            if (targetImage) {
                annotateImage(request.imageUrl, targetImage, request.settings);
                sendResponse({ success: true });
            } else {
                sendResponse({ success: false, error: "Image element not found" });
            }
        }
        
        if (request.action === "translate-text" && request.text) {
            translateText(request.text, request.settings);
            sendResponse({ success: true });
        }
        
        return true;
    });

})();
