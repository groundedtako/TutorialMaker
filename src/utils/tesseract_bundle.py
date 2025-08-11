"""
Tesseract OCR wrapper that uses bundled binaries
Automatically detects and uses the correct Tesseract installation
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional


def get_tesseract_path() -> Optional[str]:
    """
    Get the path to the Tesseract executable.
    
    Priority:
    1. Bundled Tesseract (in PyInstaller executable)
    2. System-installed Tesseract
    3. None if not found
    
    Returns:
        Path to tesseract executable or None if not found
    """
    
    # Check if running in PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        bundle_dir = Path(sys._MEIPASS)
        tesseract_bundle = bundle_dir / 'tesseract'
        
        # Check for platform-specific executable
        system = platform.system().lower()
        if system == 'windows':
            tesseract_exe = tesseract_bundle / 'tesseract.exe'
            if tesseract_exe.exists():
                return str(tesseract_exe)
        else:
            tesseract_exe = tesseract_bundle / 'bin' / 'tesseract'
            if tesseract_exe.exists():
                return str(tesseract_exe)
    
    # Check if running from source with bundled tesseract
    if os.path.exists('tesseract_bundle'):
        bundle_dir = Path('tesseract_bundle')
        system = platform.system().lower()
        
        if system == 'windows':
            tesseract_exe = bundle_dir / 'tesseract.exe'
            if tesseract_exe.exists():
                return str(tesseract_exe)
        else:
            tesseract_exe = bundle_dir / 'bin' / 'tesseract'
            if tesseract_exe.exists():
                return str(tesseract_exe)
    
    # Fall back to system-installed Tesseract
    try:
        import shutil
        system_tesseract = shutil.which('tesseract')
        if system_tesseract:
            return system_tesseract
    except ImportError:
        pass
    
    # Last resort: common installation paths
    system = platform.system().lower()
    common_paths = []
    
    if system == 'windows':
        common_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
    elif system == 'darwin':  # macOS
        common_paths = [
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',
            '/usr/bin/tesseract',
        ]
    else:  # Linux
        common_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
        ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None


def get_tessdata_path() -> Optional[str]:
    """
    Get the path to Tesseract data files.
    
    Returns:
        Path to tessdata directory or None if not found
    """
    
    # Check if running in PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_dir = Path(sys._MEIPASS)
        tessdata_dir = bundle_dir / 'tesseract' / 'tessdata'
        if tessdata_dir.exists():
            return str(tessdata_dir)
        
        # Alternative location
        tessdata_dir = bundle_dir / 'tesseract' / 'tesseract-ocr' / 'tessdata'
        if tessdata_dir.exists():
            return str(tessdata_dir)
    
    # Check if running from source with bundled tesseract
    if os.path.exists('tesseract_bundle'):
        bundle_dir = Path('tesseract_bundle')
        tessdata_dir = bundle_dir / 'tessdata'
        if tessdata_dir.exists():
            return str(tessdata_dir)
        
        # Alternative locations
        tessdata_dir = bundle_dir / 'tesseract-ocr' / 'tessdata'
        if tessdata_dir.exists():
            return str(tessdata_dir)
        
        tessdata_dir = bundle_dir / 'share' / 'tessdata'
        if tessdata_dir.exists():
            return str(tessdata_dir)
    
    # Fall back to system paths
    system = platform.system().lower()
    common_paths = []
    
    if system == 'windows':
        common_paths = [
            r'C:\Program Files\Tesseract-OCR\tessdata',
            r'C:\Program Files (x86)\Tesseract-OCR\tessdata',
        ]
    elif system == 'darwin':  # macOS
        common_paths = [
            '/usr/local/share/tessdata',
            '/opt/homebrew/share/tessdata',
            '/usr/share/tessdata',
        ]
    else:  # Linux
        common_paths = [
            '/usr/share/tesseract-ocr/tessdata',
            '/usr/local/share/tessdata',
            '/usr/share/tessdata',
        ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None


def setup_tesseract_environment():
    """
    Set up environment variables for Tesseract OCR.
    Call this before using pytesseract.
    """
    
    # Set Tesseract command path
    tesseract_cmd = get_tesseract_path()
    if tesseract_cmd:
        os.environ['TESSERACT_CMD'] = tesseract_cmd
        print(f"Using Tesseract at: {tesseract_cmd}")
        
        # Also set for pytesseract directly
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        except ImportError:
            pass
    else:
        print("WARNING: Tesseract OCR not found. OCR functionality may not work.")
    
    # Set Tesseract data path
    tessdata_path = get_tessdata_path()
    if tessdata_path:
        os.environ['TESSDATA_PREFIX'] = tessdata_path
        print(f"Using Tessdata at: {tessdata_path}")
    else:
        print("WARNING: Tessdata not found. Some OCR languages may not work.")


def verify_tesseract_installation() -> bool:
    """
    Verify that Tesseract is properly installed and accessible.
    
    Returns:
        True if Tesseract is working, False otherwise
    """
    
    tesseract_cmd = get_tesseract_path()
    if not tesseract_cmd:
        return False
    
    try:
        import subprocess
        result = subprocess.run(
            [tesseract_cmd, '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"Tesseract version: {result.stdout.split()[1] if result.stdout else 'Unknown'}")
            return True
    except (subprocess.SubprocessError, FileNotFoundError, IndexError):
        pass
    
    return False


# Initialize Tesseract environment when module is imported
setup_tesseract_environment()