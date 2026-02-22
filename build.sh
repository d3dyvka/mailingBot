#!/bin/bash
# Build script for Telegram Mailer MacOS App
# This script automates the entire build process including:
# - Cleaning previous builds
# - Running PyInstaller
# - Code signing (optional)
# - Creating DMG (optional)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Telegram Mailer MacOS App Build Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Configuration
APP_NAME="TelegramMailer"
SPEC_FILE="telegram_mailer.spec"
DIST_DIR="dist"
BUILD_DIR="build"
RESOURCES_DIR="resources"
ICON_FILE="${RESOURCES_DIR}/icon.icns"

# Check if running on MacOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This script must be run on MacOS${NC}"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Checking dependencies...${NC}"
# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}PyInstaller not found. Installing dependencies...${NC}"
    pip3 install -r requirements.txt
else
    echo -e "${GREEN}✓ Dependencies are installed${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Checking resources...${NC}"
# Check if icon exists
if [ ! -f "$ICON_FILE" ]; then
    echo -e "${YELLOW}Warning: Icon file not found at ${ICON_FILE}${NC}"
    echo -e "${YELLOW}Creating a placeholder icon...${NC}"
    
    # Create resources directory if it doesn't exist
    mkdir -p "$RESOURCES_DIR"
    
    # Create a simple placeholder icon using sips (if available)
    # For now, we'll just warn the user
    echo -e "${YELLOW}⚠ No icon will be used. The app will have a default icon.${NC}"
    echo -e "${YELLOW}To add a custom icon, place icon.icns in ${RESOURCES_DIR}/${NC}"
    
    # Modify spec file to not use icon if it doesn't exist
    if [ -f "$SPEC_FILE" ]; then
        sed -i.bak "s|icon='resources/icon.icns'|icon=None|g" "$SPEC_FILE"
    fi
else
    echo -e "${GREEN}✓ Icon file found${NC}"
fi

echo ""
echo -e "${YELLOW}Step 3: Cleaning previous builds...${NC}"
# Clean previous builds
if [ -d "$DIST_DIR" ]; then
    rm -rf "$DIST_DIR"
    echo -e "${GREEN}✓ Cleaned dist directory${NC}"
fi

if [ -d "$BUILD_DIR" ]; then
    rm -rf "$BUILD_DIR"
    echo -e "${GREEN}✓ Cleaned build directory${NC}"
fi

# Remove .pyc files and __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✓ Cleaned Python cache files${NC}"

echo ""
echo -e "${YELLOW}Step 4: Running PyInstaller...${NC}"
# Run PyInstaller
python3 -m PyInstaller "$SPEC_FILE" --clean --noconfirm

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PyInstaller build completed successfully${NC}"
else
    echo -e "${RED}✗ PyInstaller build failed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 5: Verifying build...${NC}"
# Check if .app bundle was created
APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"
if [ -d "$APP_BUNDLE" ]; then
    echo -e "${GREEN}✓ App bundle created: ${APP_BUNDLE}${NC}"
    
    # Display app bundle size
    APP_SIZE=$(du -sh "$APP_BUNDLE" | cut -f1)
    echo -e "${GREEN}  Size: ${APP_SIZE}${NC}"
    
    # Check if executable exists
    EXECUTABLE="${APP_BUNDLE}/Contents/MacOS/${APP_NAME}"
    if [ -f "$EXECUTABLE" ]; then
        echo -e "${GREEN}✓ Executable found${NC}"
        
        # Check if executable is universal binary
        if command -v lipo &> /dev/null; then
            ARCHS=$(lipo -info "$EXECUTABLE" 2>/dev/null | grep "Architectures" || echo "Unknown")
            echo -e "${GREEN}  Architectures: ${ARCHS}${NC}"
        fi
    else
        echo -e "${RED}✗ Executable not found${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ App bundle not created${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 6: Code signing (optional)...${NC}"
# Ask user if they want to sign the app
read -p "Do you want to sign the app? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # List available signing identities
    echo -e "${YELLOW}Available signing identities:${NC}"
    security find-identity -v -p codesigning
    
    echo ""
    read -p "Enter your signing identity (or press Enter to skip): " SIGNING_IDENTITY
    
    if [ -n "$SIGNING_IDENTITY" ]; then
        echo -e "${YELLOW}Signing app bundle...${NC}"
        codesign --force --deep --sign "$SIGNING_IDENTITY" "$APP_BUNDLE"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ App signed successfully${NC}"
            
            # Verify signature
            echo -e "${YELLOW}Verifying signature...${NC}"
            codesign --verify --deep --strict --verbose=2 "$APP_BUNDLE"
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ Signature verified${NC}"
            else
                echo -e "${RED}✗ Signature verification failed${NC}"
            fi
        else
            echo -e "${RED}✗ Code signing failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Skipping code signing${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipping code signing${NC}"
fi

echo ""
echo -e "${YELLOW}Step 7: Testing app launch...${NC}"
read -p "Do you want to test the app now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Launching app...${NC}"
    open "$APP_BUNDLE"
    echo -e "${GREEN}✓ App launched. Check if it opens correctly.${NC}"
else
    echo -e "${YELLOW}⚠ Skipping app test${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "App location: ${GREEN}${APP_BUNDLE}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Test the app by double-clicking: ${APP_BUNDLE}"
echo "2. If code signing was skipped, you may need to:"
echo "   - Right-click the app and select 'Open' the first time"
echo "   - Or go to System Preferences > Security & Privacy to allow it"
echo "3. To distribute the app, consider creating a DMG:"
echo "   hdiutil create -volname '${APP_NAME}' -srcfolder '${APP_BUNDLE}' -ov -format UDZO '${APP_NAME}.dmg'"
echo ""
