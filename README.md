# Looking Glass - Image Annotation Service

This service provides image annotation capabilities with optional text translation.

## Architecture

The application is organized into logical sections within a single main.py file:

### 1. Configuration and Imports
- Constants and model settings
- Logging configuration
- FastAPI app initialization

### 2. Data Models
- Label: Represents a text region with coordinates and text
- LabelWithoutText: Represents a text region with coordinates (no text)
- AnnotationResponse: Response format for annotations
- AnnotateWithoutText: Request/response format for label extraction

### 3. Agent Management
- build_chat_agent: Factory function for creating AI agents

### 4. Image Processing
- scale_image_to_size: Resizes images to target dimensions
- Language detection and label extraction functions

### 5. OCR and Translation
- Text extraction from labeled regions
- Translation functionality

### 6. API Endpoint
- /image/annotate/: Main endpoint for image annotation with optional translation

## Usage

The service provides a POST endpoint at `/image/annotate/` that accepts:
- An image file upload
- Optional `translate` parameter (boolean)
- Optional `translate_language` parameter (defaults to "english")

The endpoint returns annotated text regions with extracted text and optional translation.