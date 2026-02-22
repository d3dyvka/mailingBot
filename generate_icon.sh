#!/bin/bash
# Simple script to generate a basic icon for the app
# This creates a placeholder icon if you don't have a custom one

set -e

RESOURCES_DIR="resources"
ICON_SET_DIR="icon.iconset"
ICON_FILE="${RESOURCES_DIR}/icon.icns"

echo "Generating placeholder icon..."

# Create resources directory
mkdir -p "$RESOURCES_DIR"

# Create iconset directory
mkdir -p "$ICON_SET_DIR"

# Create a simple colored PNG using ImageMagick (if available) or sips
if command -v convert &> /dev/null; then
    echo "Using ImageMagick to create icon..."
    
    # Create base 1024x1024 image with gradient
    convert -size 1024x1024 \
        gradient:'#4A90E2-#357ABD' \
        -gravity center \
        -pointsize 200 \
        -fill white \
        -annotate +0+0 'TM' \
        temp_icon.png
    
    # Generate all required sizes
    convert temp_icon.png -resize 16x16 "${ICON_SET_DIR}/icon_16x16.png"
    convert temp_icon.png -resize 32x32 "${ICON_SET_DIR}/icon_16x16@2x.png"
    convert temp_icon.png -resize 32x32 "${ICON_SET_DIR}/icon_32x32.png"
    convert temp_icon.png -resize 64x64 "${ICON_SET_DIR}/icon_32x32@2x.png"
    convert temp_icon.png -resize 128x128 "${ICON_SET_DIR}/icon_128x128.png"
    convert temp_icon.png -resize 256x256 "${ICON_SET_DIR}/icon_128x128@2x.png"
    convert temp_icon.png -resize 256x256 "${ICON_SET_DIR}/icon_256x256.png"
    convert temp_icon.png -resize 512x512 "${ICON_SET_DIR}/icon_256x256@2x.png"
    convert temp_icon.png -resize 512x512 "${ICON_SET_DIR}/icon_512x512.png"
    convert temp_icon.png -resize 1024x1024 "${ICON_SET_DIR}/icon_512x512@2x.png"
    
    rm temp_icon.png
    
elif command -v sips &> /dev/null; then
    echo "Using sips to create icon..."
    
    # Create a simple colored square using Python
    python3 << 'EOF'
from PIL import Image, ImageDraw, ImageFont
import os

# Create a 1024x1024 image with gradient-like effect
img = Image.new('RGB', (1024, 1024), color='#4A90E2')
draw = ImageDraw.Draw(img)

# Draw a simple telegram-like icon
# Draw a paper plane shape (simplified)
draw.polygon([(200, 512), (824, 300), (824, 724)], fill='white')
draw.polygon([(200, 512), (512, 512), (512, 824)], fill='#357ABD')

# Save base image
img.save('temp_icon.png')
print("Base icon created")
EOF
    
    # Generate all required sizes using sips
    sips -z 16 16 temp_icon.png --out "${ICON_SET_DIR}/icon_16x16.png" > /dev/null 2>&1
    sips -z 32 32 temp_icon.png --out "${ICON_SET_DIR}/icon_16x16@2x.png" > /dev/null 2>&1
    sips -z 32 32 temp_icon.png --out "${ICON_SET_DIR}/icon_32x32.png" > /dev/null 2>&1
    sips -z 64 64 temp_icon.png --out "${ICON_SET_DIR}/icon_32x32@2x.png" > /dev/null 2>&1
    sips -z 128 128 temp_icon.png --out "${ICON_SET_DIR}/icon_128x128.png" > /dev/null 2>&1
    sips -z 256 256 temp_icon.png --out "${ICON_SET_DIR}/icon_128x128@2x.png" > /dev/null 2>&1
    sips -z 256 256 temp_icon.png --out "${ICON_SET_DIR}/icon_256x256.png" > /dev/null 2>&1
    sips -z 512 512 temp_icon.png --out "${ICON_SET_DIR}/icon_256x256@2x.png" > /dev/null 2>&1
    sips -z 512 512 temp_icon.png --out "${ICON_SET_DIR}/icon_512x512.png" > /dev/null 2>&1
    sips -z 1024 1024 temp_icon.png --out "${ICON_SET_DIR}/icon_512x512@2x.png" > /dev/null 2>&1
    
    rm temp_icon.png
else
    echo "Error: Neither ImageMagick nor sips is available"
    echo "Please install ImageMagick or use MacOS built-in tools"
    exit 1
fi

# Convert iconset to icns using iconutil
if command -v iconutil &> /dev/null; then
    echo "Converting to .icns format..."
    iconutil -c icns "$ICON_SET_DIR" -o "$ICON_FILE"
    
    # Clean up iconset directory
    rm -rf "$ICON_SET_DIR"
    
    echo "✓ Icon created successfully: ${ICON_FILE}"
else
    echo "Error: iconutil not found (should be available on MacOS)"
    exit 1
fi
