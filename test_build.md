# Testing TutorialMaker Executables

## Local Build Testing

### 1. Build the Executable Locally

```bash
# Install build dependencies
pip install pyinstaller pyinstaller-hooks-contrib

# Build using the spec file
pyinstaller tutorialmaker.spec --clean --noconfirm

# Check the build
ls -la dist/
```

### 2. Test the Built Executable

```bash
# Navigate to the built executable
cd dist/tutorialmaker-macos  # or tutorialmaker-linux, tutorialmaker-windows

# Run the executable
./tutorialmaker-macos  # Linux: ./tutorialmaker-linux, Windows: tutorialmaker-windows.exe
```

### 3. Quick Test Workflow

Once the executable starts, test these commands:

```bash
# In the TutorialMaker CLI:
new "Test Tutorial"           # Create a test tutorial
start                        # Start recording
# Click around your screen for a few seconds
pause                        # Test pause functionality
resume                       # Test resume
stop                         # Stop and generate tutorial
web                          # Open web interface
list                         # List tutorials
quit                         # Exit
```

### 4. Verify Bundled Components

The executable should work without any external dependencies:

**Test OCR (most important)**:
```bash
# After starting recording and making some clicks
# Check console output for OCR results like:
# "Step 1: Click on 'Button Text'"
```

**Test Web Interface**:
- After running `stop`, browser should auto-open
- Visit `http://localhost:5001`
- Should see your tutorial with screenshots
- Try editing step descriptions
- Try exporting to different formats

**Test Tesseract Bundle**:
```bash
# The app should show messages like:
# "Using Tesseract at: /path/to/bundled/tesseract"
# "Tesseract version: 5.x.x"
```

## Testing Different Scenarios

### Basic Functionality Test
1. **Create tutorial**: `new "Basic Test"`
2. **Start recording**: `start`
3. **Make 3-5 clicks** on different UI elements
4. **Stop recording**: `stop`
5. **Verify output**: Check that HTML file opens with screenshots

### Cross-Application Test
1. Start recording
2. Click in Terminal/Command Prompt
3. Switch to Browser and click some buttons
4. Switch to a text editor and type something
5. Stop recording
6. Verify all applications were captured

### OCR Accuracy Test
1. Start recording
2. Click on buttons with clear text (like "Save", "Cancel", "OK")
3. Stop recording  
4. Check that step descriptions show the correct button text

### Web Interface Test
1. Create and record a tutorial
2. Run `web` command
3. In browser:
   - Click on steps to delete them
   - Edit step descriptions
   - Export to Word/PDF
   - Verify exported files exist and are valid

## Troubleshooting Common Issues

### Executable Won't Start
```bash
# Check for missing dependencies
ldd tutorialmaker-linux     # Linux
otool -L tutorialmaker-macos # macOS
# Should show all libraries are bundled

# Run with debug info
./tutorialmaker --debug
```

### OCR Not Working
```bash
# Check Tesseract bundling
./tutorialmaker --debug
# Look for messages like:
# "Using Tesseract at: ..."
# "Tesseract version: ..."

# If missing, check build process included tesseract_bundle/
```

### Permissions Issues
```bash
# macOS: Grant Screen Recording permission
# System Preferences > Security & Privacy > Privacy > Screen Recording

# Linux: Ensure display access
echo $DISPLAY  # Should show something like :0

# Windows: Run as administrator if needed
```

### Web Interface Not Opening
```bash
# Manually open browser
open http://localhost:5001      # macOS
xdg-open http://localhost:5001  # Linux  
start http://localhost:5001     # Windows

# Check if port is available
netstat -an | grep 5001
```

## Expected Output Examples

### Successful Start
```
TutorialMaker - Privacy-focused Tutorial Maker
===========================================
Using Tesseract at: /path/to/tutorialmaker/tesseract/bin/tesseract
Tesseract version: 5.3.3
TutorialMaker initialized successfully

System Status:
  Screen: 1920x1080 (1 monitors)
  Events: Mouse=True, Keyboard=True  
  OCR: Tesseract=True, EasyOCR=True
  Storage: 0 tutorials, 0MB

Commands:
  new <title>     - Create new tutorial
  start          - Start recording
  ...
>
```

### Successful Recording
```
> new "Test Tutorial"
New tutorial created: Test Tutorial

> start
Recording started for: Test Tutorial

> # After making some clicks:
Step 1: Click on "File"
Step 2: Click on "New Document"
Step 3: Type "Hello World"

> stop
Recording stopped. Total steps: 3
Duration: 15.2 seconds
Steps captured: 3
Tutorial saved to: /path/to/projects/tutorial_xxx/
Edit in browser: http://localhost:5001/tutorial/xxx
```

## File Size Expectations

The built executables will be fairly large due to bundled dependencies:

- **Windows**: ~400-600MB (includes Python + all libraries + Tesseract)
- **macOS**: ~350-500MB 
- **Linux**: ~300-450MB

This is normal for PyInstaller builds with ML libraries (EasyOCR, OpenCV, etc.).

## GitHub Actions Testing

Once you push to GitHub, the automated build will:

1. **Build executables** for all platforms
2. **Run test suite** before building
3. **Create downloadable artifacts**
4. **Generate releases** with installation instructions

You can download the built executables from:
- GitHub Actions "Artifacts" section (for development builds)  
- GitHub Releases page (for tagged versions)

## Manual Testing Checklist

- [ ] Executable starts without errors
- [ ] OCR engines initialize correctly
- [ ] Can create new tutorials
- [ ] Recording captures clicks accurately
- [ ] OCR extracts text from buttons/UI elements
- [ ] Web interface loads and works
- [ ] Can edit tutorial steps
- [ ] Can export to multiple formats (HTML/Word/PDF)
- [ ] All exported files are valid and readable
- [ ] No external dependencies required
- [ ] Works across different applications
- [ ] Debug mode shows click markers correctly