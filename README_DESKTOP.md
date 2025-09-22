# TutorialMaker Desktop Application

A privacy-focused, local-only screen recording tool for creating step-by-step tutorials with an intuitive desktop interface.

## ✨ Features

### 🖥️ Desktop GUI
- **Modern Interface**: Clean, intuitive Tkinter-based GUI
- **System Tray Integration**: Always-available recording controls
- **Global Hotkeys**: Start/stop recording from anywhere
- **Floating Controls**: Minimal recording panel during capture
- **Visual Indicators**: Clear recording status with red/blue tray icons

### 🎬 Recording Capabilities
- **Universal App Support**: Record from any application
- **Smart Click Detection**: Accurate click marking with percentage-based coordinates
- **Real-time OCR**: Extract text from clicked regions
- **Auto-Export**: Automatically exports to HTML, Word, and PDF when recording stops
- **Session Management**: Pause, resume, and manage recording sessions

### 🔒 Privacy & Security
- **100% Local**: No cloud dependencies, all processing happens locally
- **No Admin Required**: Works with standard user permissions
- **Cross-Platform**: Supports macOS, Windows, and Linux

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd tutorialmaker
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the desktop application:**
   
   **🚀 Desktop GUI** (recommended):
   ```bash
   python main.py --gui
   ```
   *Full desktop interface with system tray and hotkeys*
   
   **🌐 Web Interface**:
   ```bash
   python main.py --web
   ```
   *Browser-based interface for editing and management*
   
   **💻 Command Line Interface**:
   ```bash
   python main.py --cli
   ```
   *Terminal-based interface for automation*
   
   **🔧 With Debug Mode**:
   ```bash
   python main.py --debug --log-level DEBUG
   ```
   *Enables detailed logging and visual click markers*

### First Tutorial

1. **Create a new tutorial:**
   - Enter a name in the "Tutorial Name" field
   - Click "New Tutorial"

2. **Start recording:**
   - Click "Start Recording" or press `Cmd+Shift+R` (Mac) / `Ctrl+Shift+R` (Windows/Linux)
   - A floating control panel will appear

3. **Perform your actions:**
   - Click and interact with any application
   - Each action is captured with screenshots and descriptions

4. **Stop recording:**
   - Click "Stop Recording" or press `Cmd+Shift+R` again
   - Tutorial is automatically exported to HTML, Word, and PDF

5. **Edit and refine:**
   - Click "Edit in Browser" to open the web-based editor
   - Delete unwanted steps, edit descriptions, and reorder actions

## 🎮 Usage Guide

### Main Window

The main window provides:
- **Recording Controls**: Create, start, and stop recordings
- **Tutorial List**: View all your created tutorials
- **Quick Actions**: Export, edit, and delete tutorials
- **Settings**: Configure preferences and hotkeys

### System Tray

Right-click the tray icon for quick access to:
- 🎬 New Tutorial
- ▶️ Start Recording  
- ⏹️ Stop Recording
- 📊 Show Main Window
- 🌐 Open Web Editor
- ⚙️ Settings

### Global Hotkeys

| Hotkey | Action |
|--------|--------|
| `Cmd+Shift+R` (Mac)<br>`Ctrl+Shift+R` (Win/Linux) | Start/Stop Recording |
| `Cmd+Shift+P` (Mac)<br>`Ctrl+Shift+P` (Win/Linux) | Pause/Resume Recording |
| `Cmd+Shift+N` (Mac)<br>`Ctrl+Shift+N` (Win/Linux) | New Tutorial |
| `Cmd+Shift+H` (Mac)<br>`Ctrl+Shift+H` (Win/Linux) | Hide/Show Floating Controls |

### Floating Controls

During recording, a minimal control panel shows:
- 🔴 Recording indicator (red dot when active, orange when paused)
- Step count and duration
- Pause/Resume and Stop buttons
- Minimize button (collapses to small indicator)

## ⚙️ Command Line Options

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

### Examples

```bash
# Start desktop GUI (default)
python main.py

# Enable debug mode with detailed logging
python main.py --debug --log-level DEBUG

# Force web interface
python main.py --web --port 8080

# Command line interface
python main.py --cli

# Web interface without auto-opening browser
python main.py --web --no-browser
```

## 🛠️ Settings & Configuration

### Recording Settings
- **Auto-export**: Automatically export when recording stops
- **Export formats**: Choose HTML, Word, and/or PDF
- **Debug mode**: Show precise click markers on screenshots
- **Auto-pause**: Pause recording during inactivity

### Interface Settings
- **Start minimized**: Launch directly to system tray
- **Notifications**: Enable/disable system notifications
- **Floating controls**: Show controls during recording
- **Always on top**: Keep controls above other windows

### Hotkey Configuration
- Customize global keyboard shortcuts
- Platform-specific modifier keys (Cmd on Mac, Ctrl on Windows/Linux)
- Disable hotkeys by leaving fields empty

### Storage Settings
- **Base folder**: Change where tutorials are saved
- **Auto-cleanup**: Remove old tutorials automatically
- **Storage limit**: Set maximum disk usage

## 📁 File Structure

```
~/TutorialMaker/
├── projects/
│   ├── tutorial_001_login_flow/
│   │   ├── metadata.json
│   │   ├── screenshots/
│   │   │   ├── step_001.png
│   │   │   └── step_002.png
│   │   ├── steps.json
│   │   └── output/
│   │       ├── index.html
│   │       ├── tutorial.docx
│   │       └── tutorial.pdf
└── settings.json
```

## 🔧 Troubleshooting

### Common Issues

**System tray not working:**
- Install pystray: `pip install pystray`
- On Linux, ensure system tray is available
- Use `--no-tray` flag as workaround

**Global hotkeys not working:**
- Install keyboard library: `pip install keyboard`
- On macOS, requires macOS 10.15 (Catalina) or later
- Use safe version for older macOS: `python3 tutorial_maker_desktop_safe.py`
- On Linux, may require running with sudo
- Check hotkey conflicts with other applications

**Recording not capturing:**
- Grant accessibility permissions (macOS)
- Check if application requires elevated privileges
- Try different applications to isolate the issue

**Web editor not opening:**
- Check if port 5000 is available
- Try accessing http://localhost:5000 manually
- Restart the application if web server fails

### Performance Tips

- **Close unnecessary applications** during recording
- **Use debug mode sparingly** (adds processing overhead)
- **Clean up old tutorials** to free disk space
- **Adjust OCR settings** if experiencing slowdowns

## 🧰 Development

### Architecture

```
src/
├── core/           # Core recording engine
├── gui/            # Desktop GUI components
│   ├── main_window.py      # Main application window
│   ├── system_tray.py      # System tray integration
│   ├── recording_controls.py # Floating control panel
│   ├── settings_dialog.py  # Settings configuration
│   ├── hotkeys.py         # Global hotkey management
│   └── desktop_app.py     # Main application coordinator
└── web/            # Web-based editor
```

### Adding New Features

1. **Core functionality**: Add to `src/core/`
2. **GUI components**: Add to `src/gui/`
3. **Web interface**: Add to `src/web/`
4. **Update requirements.txt** for new dependencies
5. **Update this README** with usage instructions

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For issues and support:
- Check the troubleshooting section above
- Search existing GitHub issues
- Create a new issue with detailed information
- Include system information and error messages

---

**TutorialMaker Desktop** - Making screen recording and tutorial creation simple, private, and powerful. 🚀