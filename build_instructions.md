# TutorialMaker Build Instructions

This document explains how to build TutorialMaker executables for distribution.

## Prerequisites

### System Dependencies

**All Platforms:**
- Python 3.9+
- Git

**Windows:**
- Visual Studio Build Tools or Visual Studio Community
- Tesseract OCR: Download from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

**macOS:**
- Xcode Command Line Tools: `xcode-select --install`
- Homebrew: `brew install tesseract`

**Linux (Ubuntu/Debian):**
- Build essentials: `sudo apt-get install build-essential`
- Tesseract: `sudo apt-get install tesseract-ocr libtesseract-dev`

## Local Build Process

### 1. Clone and Setup
```bash
git clone https://github.com/YOUR_USERNAME/tutorialmaker.git
cd tutorialmaker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller pyinstaller-hooks-contrib
```

### 2. Build Executable
```bash
# Build using the spec file (recommended)
pyinstaller tutorialmaker.spec --clean --noconfirm

# Or build manually with all options
pyinstaller --onedir --name "tutorialmaker" \
  --add-data "src:src" \
  --hidden-import pkg_resources.py2_warn \
  --hidden-import PIL._tkinter_finder \
  --collect-all easyocr \
  --collect-all pytesseract \
  --collect-all cv2 \
  --collect-all numpy \
  --collect-all PIL \
  --collect-submodules flask \
  --no-confirm \
  --clean \
  main.py
```

### 3. Test the Build
```bash
# Navigate to dist directory
cd dist/tutorialmaker/

# Test the executable
./tutorialmaker  # Linux/macOS
tutorialmaker.exe  # Windows
```

### 4. Create Distribution Archive
```bash
# From the project root
cd dist

# Linux/macOS
tar -czf tutorialmaker-$(python -c "import platform; print(platform.system().lower())")-amd64.tar.gz tutorialmaker/

# Windows (PowerShell)
Compress-Archive -Path tutorialmaker -DestinationPath tutorialmaker-windows-amd64.zip
```

## What Gets Bundled

The PyInstaller build includes:

### Python Runtime
- Complete Python 3.9+ interpreter
- All standard library modules
- No external Python installation required

### Application Dependencies
- **OCR Engines**: Tesseract, EasyOCR with all models
- **Image Processing**: OpenCV, PIL/Pillow, NumPy
- **Web Framework**: Flask, Werkzeug, Jinja2
- **Input Monitoring**: pynput for cross-platform input capture
- **Screen Capture**: mss for screenshot functionality
- **Document Export**: python-docx, ReportLab, Markdown

### Application Files
- All source code in `src/` directory
- Web templates and static files
- Configuration files

### Platform-Specific Libraries
- Windows: Win32 APIs for system integration
- macOS: Cocoa/Foundation frameworks
- Linux: X11 libraries for display capture

## Troubleshooting Build Issues

### Common Problems

**Missing Dependencies:**
```bash
# Install missing modules
pip install <missing-module>

# Update spec file to include hidden import
# Add to hidden_imports list in tutorialmaker.spec
```

**Import Errors in Built Executable:**
```bash
# Add to hidden imports in spec file
# Test with --debug flag
pyinstaller tutorialmaker.spec --debug=all
```

**Large Executable Size:**
- Review excludes list in spec file
- Remove unused dependencies
- Use UPX compression (enabled by default)

### Platform-Specific Issues

**Windows:**
- Ensure Visual Studio Build Tools are installed
- Check PATH includes Python and pip
- Run build in Administrator mode if needed

**macOS:**
- Install Xcode Command Line Tools
- Set MACOSX_DEPLOYMENT_TARGET if targeting older macOS versions
- Check code signing if distributing

**Linux:**
- Install development headers for system libraries
- Check shared library dependencies with `ldd`
- Ensure glibc compatibility for target distributions

## Automated Builds

The project uses GitHub Actions for automated cross-platform builds:

- **Trigger**: Push to main branch or version tags
- **Platforms**: Ubuntu, Windows, macOS
- **Output**: Ready-to-distribute archives
- **Testing**: Automated test suite runs before building

See `.github/workflows/build.yml` for the complete CI/CD configuration.

## Distribution

### File Structure
Each platform build creates a directory containing:
```
tutorialmaker-<platform>/
├── tutorialmaker[.exe]     # Main executable
├── _internal/              # Python runtime and dependencies
│   ├── Python files
│   ├── Shared libraries
│   └── Data files
└── Documentation files
```

### User Installation
Users only need to:
1. Download and extract the appropriate archive
2. Install Tesseract OCR (system dependency)
3. Run the executable

No Python installation or pip packages required!

### System Requirements for End Users
- **Windows**: Windows 10 or later
- **macOS**: macOS 10.14 (Mojave) or later
- **Linux**: Modern distribution with glibc 2.17+
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 500MB for application, additional space for tutorials
- **Tesseract OCR**: Required system dependency

## Security Considerations

### Code Signing
For production releases:
- **Windows**: Sign with Authenticode certificate
- **macOS**: Sign with Developer ID certificate
- **Linux**: Consider AppImage or Snap packaging

### Antivirus False Positives
PyInstaller executables may trigger antivirus warnings:
- Submit builds to antivirus vendors for whitelisting
- Use official code signing certificates
- Build on clean, verified systems

### Privacy
- All processing remains local (no network calls for OCR)
- No telemetry or data collection
- User tutorials stored locally only