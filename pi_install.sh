#!/usr/bin/env bash

# Exit if any command fails, or if using an unassigned variable
set -euo pipefail

# 1. Define your target folder and destination
TMP_DIR=$(mktemp -d)
curl -L https://github.com/LegoBro/cautious-barnacle/archive/refs/heads/main.zip -o "$TMP_DIR/repo.zip"
unzip -q "$TMP_DIR/repo.zip" -d "$TMP_DIR"

DEVICE_FOLDER="$TMP_DIR/cautious-barnacle-main/Pi"

TARGET_DIR="$HOME/birdfeeder/" # Common location for user scripts, change as needed

echo "🚀 Starting installation for this device..."

# 2. Verify the device-specific folder exists in the download
if [ ! -d "$DEVICE_FOLDER" ]; then
    echo "❌ Error: Folder '$DEVICE_FOLDER' not found in the repository."
    exit 1
fi

# 3. Create the target destination directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# 4. Copy the device-specific files over
echo "📦 Deploying files to $TARGET_DIR..."
cp -r "$DEVICE_FOLDER"/* "$TARGET_DIR"/

# 5. Make any transferred script files executable
# (Adjust the extension if you are deploying .py, .pl, etc.)
find "$TARGET_DIR" -type f -name "*.sh" -exec chmod +x {} +

# 6. Install FFMPEG
sudo apt update && sudo apt install ffmpeg -y

# 7. Run secondary install script
bash $TARGET_DIR/install.sh

echo "✅ Installation complete! Files are successfully installed in $TARGET_DIR"
