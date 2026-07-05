# Looking Glass

An intelligent image annotation service that performs OCR (Optical Character Recognition) and optional translation using Large Language Models (LLMs). Perfect for extracting text from images, manga/comic translation workflows, and automated document processing.

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Installation

1. Clone the repository:
2. uv sync
3. uv run fastapi run main.py
4. Change translation model [common.py](app/common.py) you will also want to 
5. Copy ./image_annotator_content_scrip.js to https://violentmonkey.github.io/ (if server is running in another machine change the url in the script)
5. Right click on any image and script should label it and translate it to english.