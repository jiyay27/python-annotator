#!/bin/bash
# macOS Build Script for Phishing Annotation Tool

echo "=========================================="
echo "Phishing Annotation Tool - macOS Builder"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    echo "Please install Python from https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed."
    exit 1
fi

echo "✓ pip3 found"
echo ""

# Install required packages
echo "Installing required packages..."
pip3 install pandas pyinstaller

echo ""
echo "Building macOS application..."
echo ""

# Build the application
pyinstaller --onefile \
    --windowed \
    --name=PhishingAnnotationTool \
    --clean \
    annotation_tool.py

# Check if build succeeded
if [ -d "dist/PhishingAnnotationTool.app" ]; then
    echo ""
    echo "=========================================="
    echo "✅ BUILD SUCCESSFUL!"
    echo "=========================================="
    echo ""
    echo "Your application is ready:"
    echo "  📦 dist/PhishingAnnotationTool.app"
    echo ""
    echo "To use:"
    echo "  1. Open dist/ folder"
    echo "  2. Double-click PhishingAnnotationTool.app"
    echo "  3. If macOS blocks it (Gatekeeper):"
    echo "     - Right-click the app"
    echo "     - Select 'Open'"
    echo "     - Click 'Open' in the dialog"
    echo ""
    echo "You can move the .app file anywhere (Applications folder, Desktop, etc.)"
    echo "=========================================="
else
    echo ""
    echo "❌ BUILD FAILED"
    echo "Please check the error messages above."
    exit 1
fi
