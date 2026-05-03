#!/bin/bash
#
# Firefox Extension Packaging Script
# Packages the Image Annotator extension for Firefox
#
# Usage: ./package-firefox-extension.sh [version]
#   version: Optional version string (e.g., 1.0.1). If not provided, uses version from manifest.json
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTENSION_DIR="${SCRIPT_DIR}/image-annotator-firefox-extension"
OUTPUT_DIR="${SCRIPT_DIR}/dist"
MANIFEST_FILE="${EXTENSION_DIR}/manifest.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if extension directory exists
if [ ! -d "${EXTENSION_DIR}" ]; then
    log_error "Extension directory not found: ${EXTENSION_DIR}"
    exit 1
fi

# Check if manifest.json exists
if [ ! -f "${MANIFEST_FILE}" ]; then
    log_error "manifest.json not found: ${MANIFEST_FILE}"
    exit 1
fi

# Get version from manifest.json or use provided version
if [ -n "$1" ]; then
    VERSION="$1"
    log_info "Using provided version: ${VERSION}"
else
    VERSION=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "${MANIFEST_FILE}" | head -1 | cut -d'"' -f4)
    log_info "Using version from manifest.json: ${VERSION}"
fi

# Validate version
if [ -z "${VERSION}" ]; then
    log_error "Could not determine extension version"
    exit 1
fi

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Define output filenames
XPI_FILE="${OUTPUT_DIR}/image-annotator-${VERSION}.xpi"
ZIP_FILE="${OUTPUT_DIR}/image-annotator-${VERSION}.zip"
SOURCE_ZIP_FILE="${OUTPUT_DIR}/image-annotator-${VERSION}-source.zip"

# Clean up old packages with same version
rm -f "${XPI_FILE}" "${ZIP_FILE}"

log_info "Packaging Firefox extension version ${VERSION}..."

# Files to include in the package
FILES_TO_INCLUDE=(
    "manifest.json"
    "background.js"
    "content.js"
    "popup.html"
    "popup.js"
    "options.html"
    "options.js"
)

# Check all required files exist
for file in "${FILES_TO_INCLUDE[@]}"; do
    if [ ! -f "${EXTENSION_DIR}/${file}" ]; then
        log_error "Required file not found: ${file}"
        exit 1
    fi
done

# Check icons directory
if [ ! -d "${EXTENSION_DIR}/icons" ]; then
    log_error "Icons directory not found"
    exit 1
fi

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

# Copy files to temp directory
log_info "Copying extension files..."
for file in "${FILES_TO_INCLUDE[@]}"; do
    cp "${EXTENSION_DIR}/${file}" "${TEMP_DIR}/"
done
cp -r "${EXTENSION_DIR}/icons" "${TEMP_DIR}/"

# Create .xpi file (Firefox extension package)
log_info "Creating .xpi package..."
cd "${TEMP_DIR}"
zip -r "${XPI_FILE}" . -x "*.DS_Store" -x "__pycache__/*" -x "*.pyc"

# Create .zip file (for distribution/inspection)
log_info "Creating .zip package..."
zip -r "${ZIP_FILE}" . -x "*.DS_Store" -x "__pycache__/*" -x "*.pyc"

# Create source package (includes additional files for development)
log_info "Creating source package..."
cd "${EXTENSION_DIR}"
zip -r "${SOURCE_ZIP_FILE}" . -x "*.DS_Store" -x "__pycache__/*" -x "*.pyc" -x "*.xpi" -x "*.zip"

# Verify packages were created
if [ ! -f "${XPI_FILE}" ]; then
    log_error "Failed to create .xpi package"
    exit 1
fi

if [ ! -f "${ZIP_FILE}" ]; then
    log_error "Failed to create .zip package"
    exit 1
fi

# Display package information
log_info "Packaging complete!"
echo ""
echo "Output files:"
echo "  - ${XPI_FILE}"
ls -lh "${XPI_FILE}" | awk '{print "    Size: " $5}'
echo ""
echo "  - ${ZIP_FILE}"
ls -lh "${ZIP_FILE}" | awk '{print "    Size: " $5}'
echo ""
echo "  - ${SOURCE_ZIP_FILE}"
ls -lh "${SOURCE_ZIP_FILE}" | awk '{print "    Size: " $5}'
echo ""

# Installation instructions
log_info "To install in Firefox:"
echo "  1. Open Firefox and navigate to about:debugging"
echo "  2. Click 'This Firefox' in the left sidebar"
echo "  3. Click 'Load Temporary Add-on...'"
echo "  4. Select the manifest.json file from the extension directory"
echo ""
echo "Or for permanent installation:"
echo "  1. Rename .xpi to .zip and extract"
echo "  2. Use Firefox's extension signing process for distribution"
echo ""

log_info "Done!"
