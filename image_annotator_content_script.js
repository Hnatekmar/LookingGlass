// ==UserScript==
// @name         Image Annotator
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Annotate images using AI
// @author       You
// @match        https://*/*
// @run-at       document-end
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @grant        GM_addContextMenuItem\n// ==/UserScript==

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

            // Ensure image parent has relative positioning (not the image itself)
            const parent = imageElement.parentNode;
            const originalPosition = window.getComputedStyle(parent).position;
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

            // Create container positioned relative to parent
            const labelContainer = document.createElement('div');
            labelContainer.className = 'image-label-container';
            labelContainer.dataset.imageId = getImageId(imageElement);
            labelContainer.style.cssText = `
                position: absolute;
                top: ${imageElement.offsetTop}px;
                left: ${imageElement.offsetLeft}px;
                width: ${width}px;
                height: ${height}px;
                pointer-events: none;
                z-index: 100;
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

                // Rescale normalized coordinates to pixel values
                const x1 = label.x1;
                const y1 = label.y1;
                const x2 = label.x2;
                const y2 = label.y2;

                const labelWidth = x2 - x1;
                const labelHeight = y2 - y1;

                // Calculate position and dimensions using normalized coordinates
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
                    cursor: pointer;  // Add pointer cursor to indicate clickable
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
            imageElement.insertAdjacentElement('afterend', labelContainer);

        } catch (error) {
            console.error("Error displaying labels:", error);
        }
    }

    // Function to show results in a popup
    // Params:
    //   results @type Object - The annotation results from the backend
    //   imageDimensions @type Object - Optional image dimensions for scaling
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
    function translateText(text, selection) {
        const loadingIndicator = document.createElement('div');
        loadingIndicator.textContent = 'Translating...';
        loadingIndicator.style.position = 'fixed';
        loadingIndicator.style.top = '10px';
        loadingIndicator.style.right = '10px';
        loadingIndicator.style.background = 'black';
        loadingIndicator.style.border = '1px solid #ccc';
        loadingIndicator.style.padding = '15px';
        loadingIndicator.style.borderRadius = '5px';
        loadingIndicator.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2);'
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

        GM_xmlhttpRequest({
            method: "POST",
            url: 'http://localhost:8000/translate?target_language=english',
            headers: {
                "Content-Type": "application/json"
            },
            data: JSON.stringify({ text: text }),
            onload: function(response) {
                const result = JSON.parse(response.responseText);
                console.log('Translation result:', result);

                if (result.translated_text) {
                    const range = selection.getRangeAt(0);
                    const span = document.createElement('span');
                    span.textContent = result.translated_text;
                    range.deleteContents();
                    range.insertNode(span);
                }

                if (loadingIndicator.parentNode) {
                    loadingIndicator.parentNode.removeChild(loadingIndicator);
                }
            },
            onerror: function(error) {
                console.error('Error translating text:', error);
                if (loadingIndicator.parentNode) {
                    loadingIndicator.parentNode.removeChild(loadingIndicator);
                }
            }
        });
    }

    // Function to annotate an image
    function annotateImage(imageUrl, imageElement) {
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
        loadingIndicator.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2);'
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

        // Disable context menu for all images during processing
        const originalContextMenuHandler = document.oncontextmenu;
        document.oncontextmenu = function(e) {
            if (loadingIndicator.parentNode) {
                e.preventDefault();
                return false;
            }
            return originalContextMenuHandler ? originalContextMenuHandler(e) : true;
        };

        // Use GM_xmlhttpRequest to fetch the image (bypasses CORS)
        GM_xmlhttpRequest({
            method: "GET",
            url: imageUrl,
            responseType: "blob",
            onload: function(response) {
                const blob = response.response;

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
                    canvas.toBlob(async function(resizedBlob) {
                        try {
                            // Send to backend
                            const formData = new FormData();
                            formData.append('data', resizedBlob, 'image.jpg');

                            // Use GM_xmlhttpRequest instead of fetch
                            GM_xmlhttpRequest({
                                method: "POST",
                                url: 'http://localhost:8000/image/annotate?translate=true&translate_language=english',
                                data: formData,
                                onload: function(response) {
                                    const result = JSON.parse(response.responseText);
                                    console.log('Annotation result:', result);
                                    // Show results in a popup or notification
                                    showResults(result);
                                    console.log("Labeling image");

                                    // Display labels directly on image
                                    console.log("Original image element:", imageElement);
                                    displayLabelsOnImage(result.labels, imageElement, {width: imageElement.width, height: imageElement.height});

                                    // Remove loading indicator
                                    if (loadingIndicator.parentNode) {
                                        loadingIndicator.parentNode.removeChild(loadingIndicator);
                                    }

                                    // Restore context menu
                                    document.oncontextmenu = originalContextMenuHandler;
                                },
                                onerror: function(error) {
                                    console.error('Error annotating image:', error);
                                    // Remove loading indicator on error
                                    if (loadingIndicator.parentNode) {
                                        loadingIndicator.parentNode.removeChild(loadingIndicator);
                                    }

                                    // Restore context menu
                                    document.oncontextmenu = originalContextMenuHandler;
                                }
                            });
                        } catch (error) {
                            console.error('Error annotating image:', error);
                            // Remove loading indicator on error
                            if (loadingIndicator.parentNode) {
                                loadingIndicator.parentNode.removeChild(loadingIndicator);
                            }

                            // Restore context menu
                            document.oncontextmenu = originalContextMenuHandler;
                        }
                    }, 'image/jpeg', 0.9);
                };

                img.onerror = function() {
                    console.error('Error loading image from blob');
                    URL.revokeObjectURL(objectUrl);
                    if (loadingIndicator.parentNode) {
                        loadingIndicator.parentNode.removeChild(loadingIndicator);
                    }
                    document.oncontextmenu = originalContextMenuHandler;
                };

                img.src = objectUrl;
            },
            onerror: function(error) {
                console.error('Error fetching image:', error);
                if (loadingIndicator.parentNode) {
                    loadingIndicator.parentNode.removeChild(loadingIndicator);
                }
                document.oncontextmenu = originalContextMenuHandler;
            }
        });
    }

    console.log("Script loaded");
    console.log("GM_addContextMenuItem available:", typeof GM_addContextMenuItem === 'function');

    // Add styles for popup
    GM_addStyle(`
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
        .annotation-label {
            margin: 5px 0;
            padding: 5px;
            border-bottom: 1px solid #eee;
        }
        .image-label {
            position: absolute;
            transform: translate(-50%, -100%);
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-family: Arial, sans-serif;
            white-space: nowrap;
            pointer-events: none;
        }
    `);

    // Add context menu items
    console.log("Adding Translate Image context menu");\nGM_addContextMenuItem("Translate Image", function(info) {\n    if (info.srcUrl) {\n        annotateImage(info.srcUrl, info.target);\n    }\n}, { context: "image" });\n\ntry {\n    GM_addContextMenuItem("Translate Text", function(info) {\n        console.log("Translate Text info:", info);\n        if (info.selectionText) {\n            translateText(info.selectionText, info.selection);\n        }\n    }, { context: "selection" });\n} catch (e) {\n    console.error("Error adding Translate Text menu item:", e);\n}
})();
