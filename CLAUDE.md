# Scribe Local - Screen Recording Tutorial Maker

## CRITICAL DEVELOPMENT GUIDELINES

### Cross-Platform Compatibility Requirements
- **NEVER use emojis or non-ASCII characters in code, console output, or file content**
- **NEVER use Unicode symbols in terminal output, error messages, or logging**
- **Windows/Unix compatibility**: Use only standard ASCII characters (codes 32-126)
- **File paths**: Use Path() objects with forward slashes for cross-platform compatibility
- **Console output**: Plain text only - no emojis, Unicode symbols, or fancy characters
- **Code comments and docstrings**: ASCII characters only
- **User-facing messages**: Standard ASCII text only

### Examples of FORBIDDEN content:
```
NEVER USE: 🎯 ✅ ❌ 🚀 📁 → ← ↑ ↓ • ▼ ▲ ┌ ┐ ├ ┤ é ñ ü
```

### Approved alternatives:
```
Use: "SUCCESS:" "ERROR:" "INFO:" "->" "<-" "*" "-" "+" "|" 
```

## Project Overview
A privacy-focused, local-only screen recording tool that captures user interactions (mouse clicks, keystrokes) and generates shareable tutorials. Inspired by the original Scribe tool, but runs entirely locally without requiring admin privileges or cloud connectivity.

## Core Features

### Screen Capture & Monitoring
- **Generic Event Capture**: Monitor ALL mouse clicks and keystrokes regardless of application
- **Permission-Aware**: Graceful fallback when global monitoring isn't available
- **Cross-Platform**: Support for both Windows and Mac
- **Real-time OCR**: Extract text from clicked regions to understand context
- **Smart Region Detection**: Intelligently determine UI element boundaries

### Session Management
- **Recording Control**: Start, pause, resume, stop recording sessions
- **Smart Filtering**: Skip events during pauses and from recorder app itself
- **Session Metadata**: Track duration, step count, applications used

### Output & Sharing
- **Multiple Formats**: HTML (with editing), Word documents, PDF
- **Local Web Server**: Localhost interface for post-capture editing
- **History Management**: Browse, search, and manage all created tutorials
- **Privacy-First**: Everything stored and processed locally

## Technical Architecture

### Event Monitoring System
```python
# Universal event capture
- Mouse clicks: (x, y, timestamp, button_type)
- Keystrokes: (key, timestamp, modifiers)
- Screenshots: Immediate capture on each click
- OCR Processing: Extract text from click regions
```

### Permission Model
- **No Admin Required**: Uses standard user permissions only
- **Graceful Degradation**: Multiple fallback modes if permissions limited
- **Cross-Platform APIs**: 
  - Windows: GetDC, pynput for events
  - Mac: CGWindowListCreateImage, accessibility permissions

### Local Storage Structure
```
~/TutorialMaker/
├── projects/
│   ├── tutorial_001_login_flow/
│   │   ├── metadata.json
│   │   ├── screenshots/
│   │   ├── events.json
│   │   └── output/
│   │       ├── index.html (editable)
│   │       ├── tutorial.docx
│   │       └── tutorial.pdf
└── templates/
```

### Technology Stack
- **Core**: Python 3.8+
- **Screenshot**: `mss` (cross-platform)
- **OCR**: `pytesseract` + `easyocr` (local only)
- **Computer Vision**: `opencv-python`, `pillow`, `numpy`
- **Event Monitoring**: `pynput` (cross-platform)
- **Web Interface**: Flask (localhost server)
- **Document Export**: `python-docx`, `reportlab`
- **GUI**: `tkinter` or `PyQt` for main interface

## Implementation Plan

### Phase 1: Core Capture System ✅ (Planned)
- [ ] Cross-platform screenshot capture
- [ ] Mouse click monitoring with coordinate capture
- [ ] Basic OCR integration for clicked regions
- [ ] Simple event storage system
- [ ] Basic session start/stop functionality

### Phase 2: Intelligence Layer
- [ ] Smart UI element boundary detection
- [ ] Improved OCR with preprocessing
- [ ] Keystroke grouping and text reconstruction
- [ ] Event classification (click, type, special keys)
- [ ] Context-aware step description generation

### Phase 3: Session Management
- [ ] Recording pause/resume functionality
- [ ] Event filtering during pauses
- [ ] Session metadata tracking
- [ ] Auto-save and recovery
- [ ] Session history management

### Phase 4: Output Generation
- [ ] HTML export with editing capabilities
- [ ] Word document export
- [ ] PDF export
- [ ] Local web server for editing interface
- [ ] Step deletion and reordering

### Phase 5: Post-Capture Editing
- [ ] Web-based tutorial editor
- [ ] Click-to-delete steps (Scribe-like)
- [ ] Step description editing
- [ ] Step reordering (drag-and-drop)
- [ ] Tutorial history browser

### Phase 6: Polish & Enhancement
- [ ] Performance optimizations
- [ ] Error handling and recovery
- [ ] User preferences and settings
- [ ] Export customization options
- [ ] Search and filtering capabilities

## Key Design Decisions

### Privacy & Security
- **No Cloud Dependencies**: All processing happens locally
- **No Admin Privileges**: Uses standard user permissions only
- **Local-Only OCR**: No data sent to external services
- **User Control**: Clear session boundaries and data ownership

### User Experience
- **Universal Compatibility**: Works with any application
- **Minimal Interruption**: Background monitoring with optional hotkeys
- **Immediate Feedback**: Real-time step generation and preview
- **Familiar Interface**: Scribe-like editing experience

### Technical Choices
- **Permission-Friendly**: Multiple fallback modes for different security contexts
- **Cross-Platform**: Single codebase works on Windows and Mac
- **Extensible**: Easy to add new export formats or processing logic
- **Performance**: Efficient screenshot handling and OCR caching

## Development Notes

### Current Session Progress
- Planning phase completed
- Architecture designed
- Technical stack selected
- Ready to begin implementation

### Next Steps
1. Set up project structure and dependencies
2. Implement basic screenshot capture
3. Add mouse click monitoring
4. Integrate OCR for clicked regions
5. Create simple session management

### Testing Strategy
- Unit tests for core components
- Integration tests for cross-platform compatibility
- Manual testing with various applications
- Performance testing with long recording sessions

## Usage Examples

### Basic Workflow
1. Launch TutorialMaker app
2. Click "Start Recording"
3. Perform actions in any application
4. Click "Stop Recording"
5. Review and edit captured steps
6. Export to desired format(s)

### Advanced Features
- Pause recording to skip irrelevant actions
- Edit step descriptions post-capture
- Delete unwanted steps
- Reorder steps via drag-and-drop
- Search tutorial history
- Export to multiple formats simultaneously

---

*This document serves as the living specification and progress tracker for the Scribe Local project.*