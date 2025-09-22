# TutorialMaker

**Privacy-focused, local-only screen recording tool for creating step-by-step tutorials**

![Platform Support](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Build Status](https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/tutorialmaker/build.yml?branch=main)

TutorialMaker automatically captures your screen interactions and creates professional tutorials. Record once, export to multiple formats, edit with ease - all while keeping your data completely private and local.

## ✨ Features

- 🎬 **Automatic Recording** - Captures mouse clicks, keystrokes, and screenshots
- 🧠 **Smart OCR** - Recognizes text in buttons, fields, and UI elements
- 🌐 **Web Editor** - Browser-based editing for easy customization
- 📄 **Multiple Exports** - HTML, Word, PDF, and Markdown formats
- 🔒 **100% Local** - No cloud dependencies, complete privacy
- 🖥️ **Cross-Platform** - Windows, macOS, and Linux support
- ⚡ **No Setup** - Self-contained executables, no Python installation needed

## 🚀 Quick Start

### Download & Run
1. **Download** the latest release for your platform:
   - [Windows](../../releases/latest) - `tutorialmaker-windows-amd64.zip`
   - [macOS](../../releases/latest) - `tutorialmaker-macos-amd64.tar.gz`
   - [Linux](../../releases/latest) - `tutorialmaker-linux-amd64.tar.gz`

2. **Extract** and run the executable - no installation required!

3. **Create your first tutorial**:
   - **Web Interface** (Default): Double-click executable → Browser opens → Click "Create New Recording"
   - **CLI Mode**: `./tutorialmaker --cli` then use commands like `new "My Tutorial"`

### Development Setup
```bash
git clone https://github.com/YOUR_USERNAME/tutorialmaker.git
cd tutorialmaker
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Command Line Options
```bash
python main.py [OPTIONS]

Options:
  --debug           Enable debug mode with precise click markers
  --log-level LEVEL Set logging level (DEBUG, INFO, WARNING, ERROR)
  --cli             Use command-line interface
  --web             Force web interface (default is desktop GUI)
  --gui             Force desktop GUI interface (default)
  --port PORT       Web server port (default: 5001)
  --no-browser      Don't open browser automatically
  --help            Show help message
```

### Logging & Debugging
- **Structured Logging**: All application events are logged with appropriate levels
- **Log Files**: Daily log files saved to `logs/tutorialmaker_YYYYMMDD.log`
- **Debug Mode**: `--debug` enables detailed logging and visual click markers
- **Log Levels**: Control verbosity with `--log-level DEBUG/INFO/WARNING/ERROR`

## 📖 How It Works

1. **Record** - Capture your screen interactions automatically
2. **Process** - AI-powered OCR extracts text from UI elements  
3. **Edit** - Use the web interface to refine your tutorial
4. **Export** - Generate professional documentation in multiple formats

## 🎯 Use Cases

- **Software Documentation** - Create user guides and help docs
- **Training Materials** - Onboard new team members
- **Bug Reports** - Show developers exactly what happened
- **Process Documentation** - Capture workflows and procedures
- **Educational Content** - Create step-by-step learning materials

## 🔧 System Requirements

- **Windows** 10 or later
- **macOS** 10.14 (Mojave) or later
- **Linux** with glibc 2.17+
- **Memory**: 4GB RAM (8GB recommended)
- **Display**: Any resolution (higher = better OCR)

## 📚 Documentation

- **[User Guide](USER_GUIDE.md)** - Complete usage instructions
- **[Build Instructions](build_instructions.md)** - Building from source
- **[Contributing Guide](CONTRIBUTING.md)** - Development workflow
- **[Changelog](CHANGELOG.md)** - Release history

## 🛠️ Development

### Architecture
- **Python Core** - Screen capture, OCR, and session management
- **Flask Web Server** - Local editing interface  
- **PyInstaller** - Self-contained executable builds
- **Cross-Platform APIs** - Native integration on each OS

### Key Components
- **Smart OCR** - Dual-engine text recognition (Tesseract + EasyOCR)
- **Event Monitoring** - Cross-platform input capture
- **Export Engine** - Multi-format document generation
- **Web Interface** - Browser-based tutorial editing

### Contributing
We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines  
- Testing procedures
- Pull request process

## 🔒 Privacy & Security

- **Local Processing** - Everything runs on your computer
- **No Data Upload** - Screenshots and text never leave your device
- **No Telemetry** - No usage tracking or analytics
- **Open Source** - Transparent, auditable code

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Tesseract OCR** - Optical character recognition engine
- **EasyOCR** - Neural network-based OCR
- **PyInstaller** - Python executable packaging
- **Flask** - Web framework for the editing interface

## 🆘 Support

- **🐛 Bug Reports** - [Create an issue](../../issues/new?template=bug_report.md)
- **💡 Feature Requests** - [Suggest a feature](../../issues/new?template=feature_request.md)
- **💬 Discussions** - [Join the discussion](../../discussions)
- **📖 Documentation** - Check the [User Guide](USER_GUIDE.md)

---

**Create tutorials effortlessly. Keep your data private. Share knowledge freely.**

[Download Latest Release](../../releases/latest) | [View Documentation](USER_GUIDE.md) | [Report Issues](../../issues)