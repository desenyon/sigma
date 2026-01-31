#!/usr/bin/env python3
"""Create a native macOS application bundle for Sigma."""

import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path


APP_NAME = "Sigma"
VERSION = "3.2.0"
BUNDLE_ID = "com.sigma.app"


ICON_SET = """
{
  "images" : [
    { "idiom" : "mac", "scale" : "1x", "size" : "16x16" },
    { "idiom" : "mac", "scale" : "2x", "size" : "16x16" },
    { "idiom" : "mac", "scale" : "1x", "size" : "32x32" },
    { "idiom" : "mac", "scale" : "2x", "size" : "32x32" },
    { "idiom" : "mac", "scale" : "1x", "size" : "128x128" },
    { "idiom" : "mac", "scale" : "2x", "size" : "128x128" },
    { "idiom" : "mac", "scale" : "1x", "size" : "256x256" },
    { "idiom" : "mac", "scale" : "2x", "size" : "256x256" },
    { "idiom" : "mac", "scale" : "1x", "size" : "512x512" },
    { "idiom" : "mac", "scale" : "2x", "size" : "512x512" }
  ],
  "info" : { "author" : "xcode", "version" : 1 }
}
"""


LAUNCHER_SCRIPT = '''#!/bin/bash
# Sigma Application Launcher

# Get the directory where the app bundle is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../Resources" && pwd )"

# Set up environment
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Find Python - prefer Homebrew Python 3
if command -v python3.12 &> /dev/null; then
    PYTHON="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
else
    osascript -e 'display dialog "Python 3 is required but not found. Please install Python via Homebrew: brew install python" buttons {"OK"} default button 1 with icon stop with title "Sigma Error"'
    exit 1
fi

# Check if sigma is installed
if ! $PYTHON -c "import sigma" 2>/dev/null; then
    # Try to install sigma
    $PYTHON -m pip install sigma-terminal --quiet 2>/dev/null || true
fi

# Run Sigma with Textual in a proper terminal context
# This uses the Terminal.app to run the TUI properly
exec $PYTHON -m sigma
'''


LAUNCHER_SWIFT = '''
import Cocoa
import Foundation

@main
class AppDelegate: NSObject, NSApplicationDelegate {
    var task: Process?
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        runSigma()
    }
    
    func runSigma() {
        let bundle = Bundle.main
        let resourcePath = bundle.resourcePath ?? ""
        
        // Find Python
        let pythonPaths = [
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            "/usr/bin/python3"
        ]
        
        var pythonPath: String?
        for path in pythonPaths {
            if FileManager.default.fileExists(atPath: path) {
                pythonPath = path
                break
            }
        }
        
        guard let python = pythonPath else {
            showError("Python 3 is required but not found.\\nPlease install Python via Homebrew:\\nbrew install python")
            NSApp.terminate(nil)
            return
        }
        
        // Run sigma module
        task = Process()
        task?.executableURL = URL(fileURLWithPath: python)
        task?.arguments = ["-m", "sigma"]
        task?.environment = ProcessInfo.processInfo.environment
        
        do {
            try task?.run()
            task?.waitUntilExit()
        } catch {
            showError("Failed to launch Sigma: \\(error.localizedDescription)")
        }
        
        NSApp.terminate(nil)
    }
    
    func showError(_ message: String) {
        let alert = NSAlert()
        alert.messageText = "Sigma Error"
        alert.informativeText = message
        alert.alertStyle = .critical
        alert.addButton(withTitle: "OK")
        alert.runModal()
    }
    
    func applicationWillTerminate(_ notification: Notification) {
        task?.terminate()
    }
}
'''


def create_app_bundle(output_dir: str = "dist"):
    """Create a macOS .app bundle for Sigma."""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    app_path = output_path / f"{APP_NAME}.app"
    
    # Remove existing app bundle
    if app_path.exists():
        shutil.rmtree(app_path)
    
    # Create directory structure
    contents = app_path / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"
    
    macos.mkdir(parents=True)
    resources.mkdir(parents=True)
    
    # Create Info.plist
    info_plist = {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleVersion": VERSION,
        "CFBundleShortVersionString": VERSION,
        "CFBundlePackageType": "APPL",
        "CFBundleSignature": "????",
        "CFBundleExecutable": APP_NAME,
        "CFBundleIconFile": "AppIcon",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
        "NSSupportsAutomaticTermination": False,
        "NSSupportsSuddenTermination": False,
        "LSApplicationCategoryType": "public.app-category.finance",
        "NSHumanReadableCopyright": f"Copyright 2024 Sigma Team. All rights reserved.",
    }
    
    with open(contents / "Info.plist", "wb") as f:
        plistlib.dump(info_plist, f)
    
    # Create launcher script
    launcher_path = macos / APP_NAME
    with open(launcher_path, "w") as f:
        f.write(LAUNCHER_SCRIPT)
    
    os.chmod(launcher_path, 0o755)
    
    # Create app icon (simple placeholder - generates an icns file)
    create_app_icon(resources / "AppIcon.icns")
    
    print(f"Created {app_path}")
    print(f"\nTo install, copy {APP_NAME}.app to /Applications/")
    print(f"  cp -r {app_path} /Applications/")
    
    return str(app_path)


def create_app_icon(icon_path: Path):
    """Create a simple app icon."""
    
    # Create iconset directory
    iconset_dir = icon_path.parent / "AppIcon.iconset"
    iconset_dir.mkdir(exist_ok=True)
    
    # Generate SVG content for the icon
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="1024" height="1024" viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1e3a8a"/>
      <stop offset="100%" style="stop-color:#0f172a"/>
    </linearGradient>
    <linearGradient id="sigma" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#60a5fa"/>
      <stop offset="100%" style="stop-color:#3b82f6"/>
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" rx="220" fill="url(#bg)"/>
  <text x="512" y="650" font-family="SF Pro Display, Helvetica, Arial" font-size="580" font-weight="bold" fill="url(#sigma)" text-anchor="middle">σ</text>
</svg>'''
    
    # Write SVG
    svg_path = iconset_dir / "icon.svg"
    with open(svg_path, "w") as f:
        f.write(svg_content)
    
    # Try to convert SVG to PNG using various methods
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    for size in sizes:
        png_name = f"icon_{size}x{size}.png"
        png_path = iconset_dir / png_name
        
        # Try using qlmanage (built into macOS)
        try:
            # For now, create a simple colored square as placeholder
            _create_simple_icon(png_path, size)
        except Exception as e:
            print(f"Warning: Could not create icon at size {size}: {e}")
    
    # Also create @2x versions
    for size in [16, 32, 128, 256, 512]:
        src = iconset_dir / f"icon_{size*2}x{size*2}.png"
        dst = iconset_dir / f"icon_{size}x{size}@2x.png"
        if src.exists():
            shutil.copy(src, dst)
    
    # Convert iconset to icns
    try:
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icon_path)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        # If iconutil fails, create a simple placeholder
        print("Warning: Could not create .icns file. Using placeholder.")
    
    # Cleanup
    shutil.rmtree(iconset_dir, ignore_errors=True)


def _create_simple_icon(path: Path, size: int):
    """Create a simple icon using Python."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create image with gradient background
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw rounded rectangle background
        padding = size // 8
        corner_radius = size // 5
        
        # Simple gradient simulation
        for y in range(size):
            r = int(30 + (15 - 30) * y / size)
            g = int(58 + (23 - 58) * y / size)
            b = int(138 + (42 - 138) * y / size)
            draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
        
        # Draw sigma symbol
        try:
            font_size = int(size * 0.5)
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            font = ImageFont.load_default()
        
        # Center the sigma
        text = "σ"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - size // 10
        
        draw.text((x, y), text, fill=(96, 165, 250, 255), font=font)
        
        img.save(path, "PNG")
        
    except ImportError:
        # PIL not available, create minimal PNG manually
        _create_minimal_png(path, size)


def _create_minimal_png(path: Path, size: int):
    """Create a minimal valid PNG file."""
    import struct
    import zlib
    
    # Create a simple blue square
    width = height = size
    
    def png_chunk(chunk_type, data):
        chunk_len = struct.pack(">I", len(data))
        chunk_crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xffffffff)
        return chunk_len + chunk_type + data + chunk_crc
    
    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = png_chunk(b'IHDR', ihdr_data)
    
    # IDAT chunk (image data)
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # Filter type: None
        for x in range(width):
            # Blue gradient
            r = 30
            g = 58
            b = 138
            raw_data += bytes([r, g, b])
    
    compressed = zlib.compress(raw_data, 9)
    idat = png_chunk(b'IDAT', compressed)
    
    # IEND chunk
    iend = png_chunk(b'IEND', b'')
    
    with open(path, 'wb') as f:
        f.write(signature + ihdr + idat + iend)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create Sigma macOS app bundle")
    parser.add_argument(
        "--output", "-o",
        default="dist",
        help="Output directory for the app bundle"
    )
    
    args = parser.parse_args()
    
    print("Creating Sigma.app bundle...")
    app_path = create_app_bundle(args.output)
    print(f"\nDone! App bundle created at: {app_path}")


if __name__ == "__main__":
    main()
