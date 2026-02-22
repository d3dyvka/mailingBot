# Application Icon

## Creating the .icns file

To create a proper MacOS icon file (.icns), follow these steps:

### Option 1: Using iconutil (Built-in MacOS tool)

1. Create a folder called `icon.iconset`
2. Add PNG images with these exact names and sizes:
   - icon_16x16.png
   - icon_16x16@2x.png (32x32)
   - icon_32x32.png
   - icon_32x32@2x.png (64x64)
   - icon_128x128.png
   - icon_128x128@2x.png (256x256)
   - icon_256x256.png
   - icon_256x256@2x.png (512x512)
   - icon_512x512.png
   - icon_512x512@2x.png (1024x1024)

3. Run the command:
   ```bash
   iconutil -c icns icon.iconset -o resources/icon.icns
   ```

### Option 2: Using online tools

1. Create a 1024x1024 PNG image with your app icon
2. Use an online converter like:
   - https://cloudconvert.com/png-to-icns
   - https://iconverticons.com/online/
3. Download the .icns file and place it in `resources/icon.icns`

### Option 3: Using sips (MacOS command-line tool)

```bash
# Create a simple icon from a PNG
sips -s format icns source.png --out resources/icon.icns
```

## Temporary Solution

For development and testing, you can use the default PyInstaller icon or create a simple colored square icon.

## Current Status

⚠️ **Action Required**: Place your icon.icns file in the `resources/` directory before building the app.

If no icon is provided, PyInstaller will use a default icon, and the build will still succeed.
