"""
Development utilities for live reloading and hot updates
"""

import time
import threading
from typing import Set, Callable

class LiveReloadManager:
    """Manages live reload state and notifications"""
    
    def __init__(self):
        self.reload_timestamp = time.time()
        self.clients: Set[Callable] = set()
        self.lock = threading.Lock()
        
    def trigger_reload(self, reason: str = "File changed"):
        """Trigger a reload for all connected clients"""
        with self.lock:
            self.reload_timestamp = time.time()
            print(f"🔄 Live reload triggered: {reason}")
            
            # Notify all connected clients
            dead_clients = []
            for client_callback in self.clients:
                try:
                    client_callback()
                except Exception:
                    dead_clients.append(client_callback)
                    
            # Clean up dead clients
            for dead_client in dead_clients:
                self.clients.discard(dead_client)
                
    def register_client(self, callback: Callable):
        """Register a client for reload notifications"""
        with self.lock:
            self.clients.add(callback)
            
    def unregister_client(self, callback: Callable):
        """Unregister a client"""
        with self.lock:
            self.clients.discard(callback)
            
    def get_reload_timestamp(self) -> float:
        """Get the last reload timestamp"""
        return self.reload_timestamp

# Global instance
live_reload_manager = LiveReloadManager()

def get_live_reload_script() -> str:
    """Generate JavaScript for live reloading in development mode"""
    return f"""
    <script>
    // Live reload functionality (development mode only)
    (function() {{
        if (typeof window.TUTORIAL_MAKER_DEV === 'undefined') {{
            window.TUTORIAL_MAKER_DEV = true;
            
            let lastReloadCheck = {live_reload_manager.get_reload_timestamp()};
            let reconnectAttempts = 0;
            const maxReconnectAttempts = 10;
            
            // Check for server changes every 2 seconds
            function checkForUpdates() {{
                fetch('/api/dev/reload-check', {{ 
                    method: 'GET',
                    cache: 'no-cache'
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.timestamp > lastReloadCheck) {{
                        console.log('🔄 Live reload: Server updated, refreshing page...');
                        // Small delay to ensure server is fully ready
                        setTimeout(() => {{
                            window.location.reload();
                        }}, 500);
                    }}
                    reconnectAttempts = 0; // Reset on successful connection
                }})
                .catch(error => {{
                    reconnectAttempts++;
                    if (reconnectAttempts <= maxReconnectAttempts) {{
                        console.log(`⚠️  Live reload: Connection lost, retrying... (${{reconnectAttempts}}/${{maxReconnectAttempts}})`);
                    }}
                    // Increase retry interval on failures
                    const retryInterval = Math.min(10000, 2000 + (reconnectAttempts * 1000));
                    setTimeout(checkForUpdates, retryInterval);
                    return;
                }});
                
                // Regular check interval
                setTimeout(checkForUpdates, 2000);
            }}
            
            // Start checking after page load
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', checkForUpdates);
            }} else {{
                checkForUpdates();
            }}
            
            // Add development indicator
            console.log('🔥 TutorialMaker Development Mode - Live reloading enabled');
            
            // Optional: Add visual indicator
            const devIndicator = document.createElement('div');
            devIndicator.innerHTML = '🔥 DEV';
            devIndicator.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                background: #ff6b35;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                z-index: 10000;
                font-family: monospace;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                opacity: 0.7;
            `;
            devIndicator.title = 'Development Mode - Live reloading active';
            document.body?.appendChild(devIndicator);
        }}
    }})();
    </script>
    """

def inject_live_reload_script(html_content: str) -> str:
    """Inject live reload script into HTML content"""
    if '</body>' in html_content:
        return html_content.replace('</body>', get_live_reload_script() + '\n</body>')
    else:
        return html_content + get_live_reload_script()