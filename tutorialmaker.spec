# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for TutorialMaker
This ensures all dependencies are bundled into the executable
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Get the current directory
current_dir = Path.cwd()
src_dir = current_dir / "src"

# Define hidden imports - all Python packages that PyInstaller might miss
hidden_imports = [
    # Core dependencies
    'pkg_resources.py2_warn',
    'pkg_resources.extern',
    
    # Image processing
    'PIL',
    'PIL._tkinter_finder',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.ImageEnhance',
    'PIL.ImageFilter',
    'PIL.ImageOps',
    
    # Computer vision
    'cv2',
    'numpy',
    'numpy.core',
    'numpy.core._methods',
    'numpy.lib.format',
    
    # OCR engines
    'pytesseract',
    'easyocr',
    'easyocr.detection',
    'easyocr.recognition',
    'easyocr.utils',
    
    # Input monitoring
    'pynput',
    'pynput.mouse',
    'pynput.keyboard',
    'pynput._util',
    
    # Screen capture
    'mss',
    'mss.base',
    'mss.exception',
    'mss.factory',
    'mss.models',
    'mss.screenshot',
    'mss.tools',
    
    # Web framework
    'flask',
    'flask.templating',
    'flask.json',
    'flask_cors',
    'werkzeug',
    'werkzeug.serving',
    'werkzeug.utils',
    'jinja2',
    'jinja2.ext',
    'markupsafe',
    
    # Document generation
    'docx',
    'python_docx',
    'reportlab',
    'reportlab.pdfgen',
    'reportlab.lib',
    'markdown',
    
    # System utilities
    'webbrowser',
    'threading',
    'queue',
    'subprocess',
    'platform',
    'tempfile',
    'shutil',
    'json',
    'time',
    'datetime',
    'pathlib',
    'uuid',
    'keyboard',
    'pystray',
    
    # Our application modules
    'src',
    'src.core',
    'src.core.app',
    'src.core.capture',
    'src.core.events',
    'src.core.ocr',
    'src.core.smart_ocr',
    'src.core.storage',
    'src.core.exporters',
    'src.core.session_manager',
    'src.core.event_filter',
    'src.core.event_monitor',
    'src.core.event_processor',
    'src.web',
    'src.web.server',
    'src.web.route_helpers',
    'src.gui',
    'src.gui.desktop_app',
    'src.gui.main_window',
    'src.gui.recording_controls',
    'src.gui.settings_dialog',
    'src.gui.system_tray',
    'src.gui.screen_selector',
    'src.utils',
    'src.utils.file_utils',
    'src.utils.api_utils',
]

# Define data files to include
datas = [
    # Application source code
    (str(src_dir), 'src'),
    
    # Root scripts
    ('server.py', '.'),
    ('__main__.py', '.'),
    
    # Web templates
    ('src/web/templates', 'src/web/templates'),
    ('src/web/static', 'src/web/static'),
    
    # Configuration files
    ('requirements.txt', '.'),
    ('CLAUDE.md', '.'),
    ('README.md', '.'),
    ('CHANGELOG.md', '.'),
    
    # Assets (icons, etc.)
    ('assets', 'assets'),
]

# Add Tesseract OCR binaries if available
import os
if os.path.exists('tesseract_bundle'):
    datas.append(('tesseract_bundle', 'tesseract'))
    print("Adding Tesseract OCR bundle to executable")

# Collect all submodules for critical packages
collect_all = [
    'easyocr',
    'pytesseract', 
    'cv2',
    'numpy',
    'PIL',
    'flask',
    'werkzeug',
    'jinja2',
    'docx',
    'reportlab',
    'mss',
    'pynput',
]

# Platform-specific considerations
if sys.platform == 'win32':
    # Windows-specific hidden imports
    hidden_imports.extend([
        'win32api',
        'win32gui',
        'win32con',
        'win32clipboard',
        'pywintypes',
    ])
elif sys.platform == 'darwin':
    # macOS-specific hidden imports
    hidden_imports.extend([
        'Foundation',
        'Quartz',
        'AppKit',
        'objc',
    ])
elif sys.platform.startswith('linux'):
    # Linux-specific hidden imports (optional - fail gracefully if not available)
    pass

# Analysis configuration
a = Analysis(
    ['main.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'matplotlib',
        'pandas',
        'scipy',
        'sklearn',
        'tensorflow',
        'torch',
        'jupyter',
        'IPython',
        'notebook',
        'pytest',
        'sphinx',
        'tkinter.test',
        'unittest',
        'test',
        'tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Note: Removed problematic package collection loop
# Hidden imports and data files are already comprehensive above

# PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Platform-specific executable configuration
icon_path = str(current_dir / "assets" / "icon.ico")
if sys.platform == 'win32':
    exe_name = 'tutorialmaker-windows.exe'
    console = True  # Keep console for debugging; can be False for production
    icon = icon_path if os.path.exists(icon_path) else None
elif sys.platform == 'darwin':
    exe_name = 'tutorialmaker-macos'
    console = True
    # macOS uses ICNS format, but ICO will work as fallback
    icon = icon_path if os.path.exists(icon_path) else None
else:  # Linux
    exe_name = 'tutorialmaker-linux'
    console = True
    icon = icon_path if os.path.exists(icon_path) else None

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=console,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

# Collect everything into a directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=exe_name.replace('.exe', ''),  # Directory name without .exe
)

# macOS App bundle (optional)
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='TutorialMaker.app',
        icon=icon,
        bundle_identifier='com.tutorialmaker.app',
        info_plist={
            'CFBundleName': 'TutorialMaker',
            'CFBundleDisplayName': 'TutorialMaker',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'LSUIElement': False,  # Set to True to hide from dock
            'NSMicrophoneUsageDescription': 'TutorialMaker needs microphone access for recording tutorials.',
            'NSScreenCaptureUsageDescription': 'TutorialMaker needs screen recording access to capture your actions.',
            'NSAccessibilityUsageDescription': 'TutorialMaker needs accessibility access to monitor mouse and keyboard events.',
        },
    )