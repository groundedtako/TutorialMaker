# TutorialMaker - Local Screen Recording Tutorial Generator

A privacy-focused, local-only screen recording tool that captures user interactions and generates shareable tutorials. Create step-by-step guides with screenshots, OCR text extraction, and multiple export formats - all without sending data to the cloud.

## 🌟 Features

- **Universal Screen Capture**: Works with any application on Windows and Mac
- **Smart Interaction Detection**: Automatically captures mouse clicks and keystrokes
- **OCR Text Extraction**: Identifies clicked UI elements and buttons
- **Multiple Export Formats**: HTML (interactive), Word documents, Markdown, and PDF with flexible selection
- **Web-Based Editor**: Edit tutorials in your browser after recording
- **Privacy-First**: Everything runs locally - no cloud dependencies
- **No Admin Required**: Uses standard user permissions

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- macOS or Windows

### Setup
1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### macOS Additional Setup
For screen capture and accessibility features, you may need to grant permissions:
1. **Screen Recording**: System Preferences → Security & Privacy → Privacy → Screen Recording
2. **Accessibility** (for click monitoring): System Preferences → Security & Privacy → Privacy → Accessibility

## 🚀 Quick Start

### 1. Record Your First Tutorial

```bash
# Start the main application
python3 main.py

# Create a new tutorial
new "My First Tutorial"

# Start recording
start

# Perform your actions (clicks, typing, etc.)
# The app will automatically capture screenshots and detect interactions

# Stop recording when done
stop

# Exit the application
exit
```

### 2. Edit and Export with Web Interface

```bash
# Start the web server (production mode)
python3 server.py

# Or for development with live reloading
python3 server.py --dev
```

This opens your browser to `http://localhost:5001` where you can:
- **View all your tutorials** with file locations
- **Edit step descriptions** inline
- **Delete unwanted steps** with confirmation
- **Export to multiple formats** (HTML, Word, PDF)
- **Create new recordings** from the web interface
- **Smart export options** with tutorial-named files
- **Cross-platform file opening** - click any path to open in file manager

### 3. Command-Line Export (Alternative)

```bash
# Export specific tutorial
python3 export_tutorials.py --tutorial-id YOUR_TUTORIAL_ID

# Export all tutorials
python3 export_tutorials.py --all

# List available tutorials
python3 export_tutorials.py --list
```

## 🖥️ Server Modes

The unified `server.py` handles all functionality through command-line flags:

### Production Mode (Default)
```bash
python3 server.py
```
- ✅ Full recording capabilities
- ✅ Tutorial viewing and editing
- ✅ Optimized performance
- 🌐 Runs on port 5001

### Development Mode
```bash
python3 server.py --dev
```
- ✅ All production features PLUS:
- 🔥 **Live reloading** when files change
- ⚡ **Auto browser refresh** 
- 👁️ **File system watching**
- 🛠️ **Enhanced debugging**

### View-Only Mode  
```bash
python3 server.py --view-only
```
- ✅ View and edit existing tutorials
- ✅ Export functionality
- ❌ No recording capabilities
- 🎯 Use when dependencies are missing

### Other Options
```bash
python3 server.py --port 8080     # Custom port
python3 server.py --no-browser    # Don't open browser
python3 server.py --help          # Show all options
```

## 📁 File Structure

Your tutorials are stored in:
```
~/TutorialMaker/
├── projects/
│   ├── tutorial_90d54395/          # Each tutorial gets a unique folder
│   │   ├── metadata.json           # Tutorial info (title, duration, etc.)
│   │   ├── steps.json              # Step-by-step data
│   │   ├── screenshots/            # Screenshots for each step
│   │   │   ├── step_001.png
│   │   │   ├── step_002.png
│   │   │   └── ...
│   │   └── output/                 # Generated files
│   │       ├── My_Tutorial_Title.html   # Interactive tutorial (named after tutorial)
│   │       ├── My_Tutorial_Title.docx   # Word document (named after tutorial)
│   │       ├── My_Tutorial_Title.md     # Markdown document (named after tutorial)
│   │       └── My_Tutorial_Title.pdf    # PDF version (named after tutorial)
│   └── tutorial_c6501472/
└── templates/
```

## 🛠️ Usage Examples

### Recording Workflows

**Software Tutorial:**
```bash
python3 main.py
> new "How to Use Photoshop Layers"
> start
# Open Photoshop, create layers, demonstrate features
> stop
```

**Website Navigation:**
```bash
python3 main.py
> new "Online Shopping Checkout Process"
> start
# Navigate website, add items to cart, checkout
> stop
```

### Exporting Tutorials

**Export Specific Tutorial:**
```bash
# List available tutorials
python3 export_tutorials.py --list

# Export specific tutorial to HTML only
python3 export_tutorials.py --tutorial-id 90d54395 --formats html
```

**Bulk Export:**
```bash
# Export all tutorials to default formats (HTML, Word)
python3 export_tutorials.py --all

# Export all tutorials to specific formats
python3 export_tutorials.py --all --formats html word markdown pdf
```

### Web Interface Features

1. **Tutorial Management**
   - View all tutorials in a grid layout
   - See tutorial metadata (steps, duration, status)
   - Delete unwanted tutorials

2. **Step Editing**
   - Click on any step description to edit it
   - Delete steps with the × button
   - Changes are saved automatically

3. **Export Options**
   - Multi-select checkbox interface for formats
   - Choose from HTML, Word, Markdown, and PDF
   - Smart export positioning (always above button)
   - Download files directly from browser
   - Preview tutorials before sharing

## 📋 Command Reference

### Main Application (main.py)
- `new "<title>"` - Create new tutorial
- `start` - Begin recording
- `pause` - Pause recording (resume with `start`)
- `stop` - Stop recording and save
- `list` - Show all tutorials
- `status` - Show current session info
- `exit` - Quit application

### Export Tools
```bash
# List tutorials
python3 export_tutorials.py --list

# Export specific tutorial
python3 export_tutorials.py --tutorial-id <ID> --formats html word markdown pdf

# Export all tutorials
python3 export_tutorials.py --all

# Test export functionality
python3 test_export.py
```

### Web Server
```bash
# Start web interface
python3 start_web_server.py

# Server runs at http://localhost:5000
# Press Ctrl+C to stop
```

## 🎯 Export Formats

### HTML Export (Default)
- **Interactive tutorial** with embedded screenshots
- **Animated click indicators** showing where you clicked
- **Editable descriptions** (click to edit)
- **Step deletion** (click × to remove)
- **Responsive design** for mobile/desktop
- **Self-contained** (all images embedded)
- **Viewport animations** that trigger when steps come into view

### Word Document Export (Default)
- **Professional layout** with title page
- **Step-by-step instructions** with numbering
- **Embedded screenshots** with click indicators highlighted
- **Metadata included** (creation date, duration, etc.)
- **Ready for sharing** or printing

### Markdown Export
- **Developer-friendly format** perfect for documentation
- **Table of contents** with clickable links for tutorials >3 steps
- **Image references** with relative paths for portability
- **OCR text inclusion** with confidence percentages
- **Click coordinates** and action descriptions
- **Compatible** with GitHub, wikis, and documentation systems

### PDF Export (Optional)
- **Print-ready format** with professional styling
- **Optimized images** with automatic scaling
- **Page breaks** for long tutorials
- **Metadata header** with tutorial information
- **Universal compatibility** (requires explicit selection)

## 🔧 Customization

### OCR Settings
The application uses two OCR engines for text extraction:
- **Tesseract** (primary) - Fast and accurate
- **EasyOCR** (backup) - Better for complex layouts

### Screenshot Quality
Screenshots are saved as PNG files with full quality. You can modify the capture settings in `src/core/capture.py`.

### Export Templates
HTML templates can be customized in `src/core/exporters.py` to match your branding or style preferences.

## 🐛 Troubleshooting

### Common Issues

**"No module named 'mss'" Error:**
```bash
pip install -r requirements.txt
```

**Permission Denied on macOS:**
1. Go to System Preferences → Security & Privacy → Privacy
2. Add Terminal or your IDE to Screen Recording and Accessibility

**OCR Not Working:**
- Install Tesseract: `brew install tesseract` (macOS) or download from GitHub
- Ensure it's in your system PATH

**Web Server Won't Start:**
- Check if port 5000 is available: `lsof -i :5000`
- Try different port: Edit `start_web_server.py` and change the port number

### Performance Tips

- **Close unnecessary applications** during recording for better performance
- **Use shorter recording sessions** (under 50 steps) for faster processing
- **Export tutorials regularly** to avoid large data accumulation

## 🔒 Privacy & Security

- **100% Local Processing** - No data sent to external servers
- **No Cloud Dependencies** - Everything runs on your machine
- **No User Tracking** - No analytics or telemetry
- **Secure Storage** - Files stored in your home directory
- **Open Source** - Full transparency of code and processes

## 📈 Roadmap

- [ ] **Enhanced OCR** with preprocessing for better accuracy
- [ ] **Keyboard Shortcut Support** for easier recording control
- [ ] **Step Reordering** via drag-and-drop in web interface
- [ ] **Custom Export Templates** for different use cases
- [ ] **Video Export** option for animated tutorials
- [ ] **Plugin System** for custom integrations

## 🤝 Contributing

This is a local-focused tool designed for privacy and simplicity. Feel free to fork and modify for your specific needs.

## 📄 License

Open source - use and modify as needed for your tutorial creation workflow.

---

**Happy Tutorial Making! 🎬**

For support or questions, check the troubleshooting section above or review the source code in the `src/` directory.