"""
Global hotkey management for TutorialMaker
Cross-platform global keyboard shortcuts
"""

import threading
from typing import Dict, Callable, Optional, TYPE_CHECKING
import sys

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
except Exception as e:
    # Handle macOS compatibility issues or other platform-specific errors
    print(f"Warning: keyboard library not available due to compatibility issue: {e}")
    KEYBOARD_AVAILABLE = False

if TYPE_CHECKING:
    from ..core.app import TutorialMakerApp
    from .main_window import MainWindow


class GlobalHotkeyManager:
    """Manages global keyboard shortcuts"""
    
    def __init__(self, app: 'TutorialMakerApp', main_window: 'MainWindow'):
        self.app = app
        self.main_window = main_window
        self.hotkeys: Dict[str, Callable] = {}
        self.registered_hotkeys: Dict[str, object] = {}
        self.running = False
        
        if not KEYBOARD_AVAILABLE:
            print("Warning: Global hotkeys not available on this system.")
            print("This may be due to:")
            print("  - Missing keyboard library (install with: pip install keyboard)")
            print("  - macOS version compatibility (requires macOS 10.15+)")
            print("  - Platform-specific restrictions")
            print("The application will work normally without global hotkeys.")
    
    def register_hotkey(self, hotkey_combination: str, callback: Callable):
        """Register a global hotkey"""
        if not KEYBOARD_AVAILABLE:
            return False
        
        try:
            # Normalize hotkey format for different platforms
            normalized_hotkey = self._normalize_hotkey(hotkey_combination)
            
            # Store callback
            self.hotkeys[normalized_hotkey] = callback
            
            # Register with keyboard library
            keyboard.add_hotkey(normalized_hotkey, callback)
            self.registered_hotkeys[normalized_hotkey] = True
            
            print(f"✅ Registered hotkey: {hotkey_combination} -> {normalized_hotkey}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to register hotkey {hotkey_combination}: {e}")
            return False
    
    def unregister_hotkey(self, hotkey_combination: str):
        """Unregister a global hotkey"""
        if not KEYBOARD_AVAILABLE:
            return
        
        normalized_hotkey = self._normalize_hotkey(hotkey_combination)
        
        try:
            if normalized_hotkey in self.registered_hotkeys:
                keyboard.remove_hotkey(normalized_hotkey)
                del self.registered_hotkeys[normalized_hotkey]
                del self.hotkeys[normalized_hotkey]
                print(f"🗑️  Unregistered hotkey: {hotkey_combination}")
        except Exception as e:
            print(f"Error unregistering hotkey {hotkey_combination}: {e}")
    
    def _normalize_hotkey(self, hotkey: str) -> str:
        """Normalize hotkey format for cross-platform compatibility"""
        # Convert common modifier names
        replacements = {
            'cmd': 'ctrl' if sys.platform.startswith('win') else 'cmd',
            'command': 'ctrl' if sys.platform.startswith('win') else 'cmd',
            'win': 'cmd',
            'super': 'cmd',
        }
        
        normalized = hotkey.lower()
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def start(self):
        """Start hotkey monitoring"""
        if not KEYBOARD_AVAILABLE:
            return
        
        self.running = True
        print("🎹 Global hotkey monitoring started")
    
    def stop(self):
        """Stop hotkey monitoring and unregister all hotkeys"""
        if not KEYBOARD_AVAILABLE:
            return
        
        self.running = False
        
        # Unregister all hotkeys
        for hotkey in list(self.registered_hotkeys.keys()):
            try:
                keyboard.remove_hotkey(hotkey)
            except:
                pass
        
        self.registered_hotkeys.clear()
        self.hotkeys.clear()
        
        print("🛑 Global hotkey monitoring stopped")
    
    def list_hotkeys(self) -> Dict[str, str]:
        """List all registered hotkeys"""
        return {hotkey: callback.__name__ for hotkey, callback in self.hotkeys.items()}


# Platform-specific implementations could go here if needed
class MacOSHotkeyManager(GlobalHotkeyManager):
    """macOS-specific hotkey implementation"""
    pass


class WindowsHotkeyManager(GlobalHotkeyManager):
    """Windows-specific hotkey implementation"""
    pass


class LinuxHotkeyManager(GlobalHotkeyManager):
    """Linux-specific hotkey implementation"""
    pass