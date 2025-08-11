# TutorialMaker User Guide

**TutorialMaker** is a privacy-focused tool that records your screen interactions and automatically creates step-by-step tutorials. Everything runs locally on your computer - no cloud services, no data uploads.

## 🚀 Quick Start

### Installation

1. **Download TutorialMaker**
   - Go to the [Releases page](../../releases/latest)
   - Download the appropriate version for your operating system:
     - **Windows**: `tutorialmaker-windows-amd64.zip`
     - **macOS**: `tutorialmaker-macos-amd64.tar.gz`
     - **Linux**: `tutorialmaker-linux-amd64.tar.gz`

2. **Extract and Run**
   - **Windows**: Unzip the file and run `tutorialmaker-windows.exe`
   - **macOS**: Extract with `tar -xzf tutorialmaker-macos-amd64.tar.gz` then run `./tutorialmaker-macos/tutorialmaker-macos`
   - **Linux**: Extract with `tar -xzf tutorialmaker-linux-amd64.tar.gz` then run `./tutorialmaker-linux/tutorialmaker-linux`

3. **That's it!** 
   - No Python installation required
   - No additional dependencies needed
   - All OCR engines are bundled

### First Tutorial

1. **Launch TutorialMaker** - The application starts the web interface automatically
2. **Browser opens** - TutorialMaker opens at `http://localhost:5001`
3. **Create a tutorial** - Click "Create New Recording" and enter a name
4. **Start recording** - Click "Start Recording" 
5. **Perform your actions** - Click around, type text, interact with any application
6. **Stop recording** - Click "Stop Recording" in the web interface
7. **Edit your tutorial** - Use the web interface to edit, delete steps, and export

## 📖 How It Works

### What Gets Recorded
- **Mouse Clicks**: Every click is captured with precise location
- **Keyboard Input**: Text entry and special keys (Enter, Tab, etc.)
- **Screen Context**: Screenshots of what you clicked on
- **Text Recognition**: Automatic OCR to understand what you clicked

### Smart Features
- **Automatic Step Generation**: Each action becomes a tutorial step
- **Intelligent Text Extraction**: Recognizes buttons, fields, and UI elements
- **Multi-Application Support**: Record across any software
- **Privacy-First**: Everything stays on your computer

## 🖥️ Application Modes

TutorialMaker offers two ways to use it:

### 1. Web Interface (Default)
The main executable starts a web server and opens your browser:

```bash
./tutorialmaker              # Starts web interface (default)
./tutorialmaker --port 8080  # Custom port
./tutorialmaker --debug      # Debug mode with click markers
```

Features:
- **Create & Record**: Start new recordings directly in browser
- **Edit**: Modify step descriptions, delete unwanted steps
- **Export**: Download as HTML, Word, PDF, or Markdown
- **Manage**: Browse, search, and organize tutorials
- **Share**: Export files are ready to share

### 2. Command Line Interface (Optional)
Advanced users can use the CLI mode:

```bash
./tutorialmaker --cli        # Use CLI instead of web interface
```

CLI Commands:
```bash
# Tutorial Management
new "Tutorial Title"          # Create new tutorial
start                        # Start recording
pause                        # Pause recording
resume                       # Resume recording  
stop                         # Stop and save tutorial

# Viewing & Management
list                         # List all tutorials
status                       # Show current status
web                          # Open web editor
debug                        # Toggle debug mode
quit                         # Exit application
```

## 🎯 Recording Tips

### Best Practices
1. **Plan Your Actions** - Think through the workflow before recording
2. **Click Deliberately** - Clear, intentional clicks work best
3. **Pause When Needed** - Use pause/resume for interruptions
4. **Use Debug Mode** - Add `--debug` flag to see exactly where clicks are detected

### What to Avoid
- **Rapid Clicking** - Give each action a moment to process
- **Mouse Dragging** - Focus on clicks rather than drags
- **Private Information** - Remember everything is captured in screenshots

### Optimizing OCR
- **High Contrast** - Dark text on light backgrounds works best
- **Standard Fonts** - Avoid unusual or decorative fonts
- **Good Resolution** - Higher resolution screens give better text recognition

## 📂 File Organization

TutorialMaker creates this folder structure:

```
~/TutorialMaker/                    # Main folder in your home directory
├── projects/                      # All your tutorials
│   └── tutorial_001_login/        # Individual tutorial folder
│       ├── metadata.json          # Tutorial info
│       ├── events.json            # Recorded actions
│       ├── screenshots/           # Screen captures
│       │   ├── step_001.png
│       │   └── step_002.png
│       └── output/                # Exported files
│           ├── index.html         # Editable HTML version
│           ├── tutorial.docx      # Word document
│           ├── tutorial.pdf       # PDF version
│           └── tutorial.md        # Markdown version
```

## 🔧 Advanced Features

### Debug Mode
Add `--debug` when launching to see:
- Red dots showing exact click locations
- Additional console output for troubleshooting
- OCR processing details

```bash
./tutorialmaker --debug
```

### Export Formats

**HTML** (default)
- Interactive, editable in browser
- Click steps to delete them
- Edit descriptions inline
- Best for sharing and further editing

**Word Document (.docx)**
- Professional document format
- Screenshots with descriptions
- Ready for corporate documentation

**PDF**
- Universal, non-editable format
- Perfect for final distribution
- Consistent across all devices

**Markdown**
- Plain text with formatting
- Great for GitHub, wikis
- Easy to version control
- Requires screenshots folder for sharing

## 📤 Sharing Tutorials

### Quick Sharing Guide

**For Email/Instant Sharing:**
- Use **HTML format** - completely self-contained, works anywhere
- Use **Word (.docx)** or **PDF** - images embedded, no extra files needed

**For Wikis/Documentation:**
- Use **Markdown** with screenshots folder - perfect for GitHub, GitLab
- Use **HTML** for standalone web pages

### Sharing Methods by Format

#### HTML Format (Recommended for Email)
```bash
# Files to share:
tutorial_name.html  # Single file, everything included
```
**Perfect for:**
- Email attachments (single file)
- Web hosting (upload one file)
- Instant sharing (double-click to view)
- Offline viewing (works without internet)

**How to share:**
1. Export tutorial as HTML
2. Find file in: `~/TutorialMaker/projects/your-tutorial/output/tutorial_name.html`
3. Attach single HTML file to email
4. Recipient opens in any web browser

#### Markdown Format (Best for Documentation)
```bash
# Files to share:
tutorial_name.md           # The tutorial content
screenshots/               # Folder with all images
├── login_tutorial_abcd1234_step_001.png
├── login_tutorial_abcd1234_step_002.png
└── login_tutorial_abcd1234_step_003.png
```
**Perfect for:**
- GitHub repositories/wikis
- Documentation sites
- Version control systems
- Technical documentation

**How to share:**
1. Export tutorial as Markdown
2. Compress tutorial folder: `~/TutorialMaker/projects/your-tutorial/`
3. Share the ZIP file or upload to GitHub/GitLab
4. Images automatically display in Markdown viewers

**Note:** Screenshots are uniquely named with tutorial title and ID hash to prevent conflicts when sharing multiple tutorials.

#### Word/PDF Format (Professional Documents)
```bash
# Files to share:
tutorial_name.docx  # or tutorial_name.pdf
```
**Perfect for:**
- Corporate documentation
- Training manuals
- Formal documentation
- Print-ready materials

### Web Server Mode
The app includes a local web server for editing:
- Launches automatically after recording
- Available at `http://localhost:5001`
- Edit tutorials in your browser
- Export to multiple formats simultaneously

## 🛠️ Troubleshooting

### Common Issues

**"Permission Denied" Errors**
- macOS: Grant screen recording permissions in System Preferences → Security & Privacy
- Windows: Run as administrator if needed
- Linux: Install with proper user permissions

**OCR Not Working**
- OCR engines are bundled - no separate installation needed
- Try debug mode to see what text is detected
- Higher resolution displays give better results

**Recording Not Capturing**
- Check that you have screen recording permissions
- Try running in debug mode to see click detection
- Ensure the app has focus when starting recording

**Web Interface Not Opening**
- Manually visit `http://localhost:5001`
- Check if port 5001 is available
- Try the `web` command to restart the server

### Getting Help

**Console Output**
The application shows helpful messages:
- Recording status updates
- OCR processing results  
- Error messages with context

**Debug Information**
Use `--debug` flag for detailed information:
- Click coordinate detection
- OCR processing steps
- Screenshot capture details

## 🔒 Privacy & Security

### Local-Only Processing
- **No Internet Required**: Everything runs on your computer
- **No Data Upload**: Screenshots and text never leave your device
- **No Telemetry**: No usage tracking or analytics
- **Open Source**: Code is transparent and auditable

### File Security
- Tutorials stored in your home directory
- Standard file permissions apply
- You control all data - delete anytime
- Export formats don't contain metadata

### Screen Recording Permissions
- **macOS**: Requires Screen Recording permission (prompted first time)
- **Windows**: May require elevated privileges for global input monitoring
- **Linux**: Uses standard X11 permissions

## 🆘 Support

### Documentation
- **CHANGELOG.md**: Latest features and fixes
- **CONTRIBUTING.md**: Development and contribution guide  
- **Build Instructions**: For building from source

### Community
- **Issues**: Report bugs or request features on GitHub
- **Discussions**: Community help and feature discussions
- **Releases**: Download latest versions and see release notes

### System Requirements
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Disk Space**: 500MB for application, additional space for tutorials
- **Display**: Any resolution (higher resolution = better OCR)
- **OS Version**: 
  - Windows 10 or later
  - macOS 10.14 (Mojave) or later  
  - Linux with glibc 2.17+

---

**Happy Tutorial Making!** 🎬

Create professional tutorials in minutes, share knowledge effortlessly, and keep your privacy intact.