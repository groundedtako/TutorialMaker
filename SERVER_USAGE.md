# TutorialMaker Unified Web Server

## Single Server, All Features

The new unified server handles everything through command-line options:

```bash
python3 server.py                    # Production mode
python3 server.py --dev              # Development mode with live reload
python3 server.py --view-only        # View-only mode (no recording)
python3 server.py --port 8080        # Custom port
python3 server.py --dev --no-browser # Dev mode without opening browser
```

## Usage Examples

### Production Mode (Default)
```bash
python3 server.py
```
- ✅ Full recording capabilities
- ✅ Tutorial viewing/editing
- ✅ Optimized performance
- ✅ Auto-detects available dependencies
- 🌐 Port: 5001

### Development Mode  
```bash
python3 server.py --dev
```
- ✅ All production features PLUS:
- 🔥 **Live reloading** when files change
- ⚡ **Auto browser refresh**
- 🛠️ **Enhanced error reporting**  
- 👁️ **File system watching**
- 🔄 **Hot module reloading**

### View-Only Mode
```bash
python3 server.py --view-only
```
- ✅ View and edit existing tutorials
- ✅ Export to HTML/Word/PDF
- ✅ Tutorial management
- ❌ No recording capabilities
- 🎯 Use when: Dependencies missing or just managing tutorials

### Custom Port
```bash
python3 server.py --port 8080
```
- 🌐 Run on any port you want
- 🔧 Useful for avoiding port conflicts

## Features Available

### All Modes Include:
- ✅ View and edit existing tutorials
- ✅ Export to HTML/Word/PDF with tutorial names
- ✅ Smart export dropdown menus
- ✅ Cross-platform file opening
- ✅ Tutorial renaming and deletion
- ✅ File location display with click-to-open

### Recording Mode Additional Features:
- ✅ Create new tutorials with custom names
- ✅ Start/Pause/Resume/Stop recording
- ✅ Real-time recording status display  
- ✅ Screenshot capture with OCR
- ✅ Mouse click and keyboard monitoring

### Development Mode Additional Features:
- 🔥 **Live file watching** (.py, .html, .css, .js files)
- ⚡ **Automatic server restart** on Python changes
- 🔄 **Automatic browser refresh** on any file change
- 👁️ **Visual dev indicator** (🔥 DEV badge)
- 🛠️ **Enhanced debugging** with detailed logs

## Quick Start

### For Regular Use:
```bash
python3 server.py
```

### For Development:
```bash
python3 server.py --dev
```

## Advanced Options

```bash
python3 server.py --help
```

Shows all available options:
- `--dev` / `--development`: Enable development mode
- `--port PORT` / `-p PORT`: Set custom port  
- `--view-only`: Disable recording features
- `--no-browser`: Don't open browser automatically
- `--debug`: Enable Flask debug mode

## Troubleshooting

### Port Already in Use
```bash
# Kill existing server on port 5001
lsof -ti:5001 | xargs kill

# Or use different port
python3 server.py --port 8080
```

### Missing Dependencies
The server auto-detects available dependencies:
```bash
# Install all dependencies
pip install -r requirements.txt

# If some dependencies fail, server will fallback gracefully
python3 server.py --view-only
```

### Development Mode Issues
```bash
# If live reload not working, missing watchdog:
pip install watchdog

# Fallback to production mode:
python3 server.py
```

### File Changes Not Reloading
1. Check for 🔥 DEV indicator in browser top-right
2. Look for file watching messages in terminal
3. Only these file types trigger reload: `.py`, `.html`, `.css`, `.js`

## Single Code Path

✅ **No more separate dev/production servers!**
- Same code handles all modes
- Development features are optional flags
- No risk of dev/prod inconsistencies
- Easier maintenance and testing