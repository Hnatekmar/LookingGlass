"""pytest configuration - set required environment variables for tests."""
import os

# Set required environment variables before any app imports
os.environ.setdefault("IMAGE_MODEL", "test-model")
os.environ.setdefault("TRANSLATION_MODEL", "test-translator")
os.environ.setdefault("IMAGE_MODEL_URL", "http://localhost:8000/v1")
os.environ.setdefault("TRANSLATION_MODEL_URL", "http://localhost:8001/v1")
os.environ.setdefault("GEMMA_OCR_URL", "http://localhost:8010/v1")
os.environ.setdefault("GEMMA_OCR_MODEL", "gemma-12b-test")
os.environ.setdefault("OCR_PROVIDER", "glm_ocr")
