"""
Cross-platform file system utilities
Handles file operations and path opening across Windows, macOS, and Linux
"""

import os
import platform
import re
import subprocess
from pathlib import Path
from typing import Optional


def format_duration(duration: float) -> str:
    """Format duration in seconds to human-readable format"""
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    return f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitize filename for cross-platform compatibility
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename safe for all platforms
    """
    if not filename:
        return "untitled"
    
    # Remove or replace problematic characters
    # Windows forbidden: < > : " | ? * \ /
    # Also remove control characters
    sanitized = re.sub(r'[<>:"|?*\\/\x00-\x1f]', '_', filename)
    
    # Remove multiple consecutive underscores/spaces
    sanitized = re.sub(r'[_\s]+', '_', sanitized)
    
    # Remove leading/trailing spaces and dots (Windows issues)
    sanitized = sanitized.strip(' .')
    
    # Truncate to max length while preserving extension
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')
    
    # Fallback if empty
    return sanitized if sanitized else "untitled"


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in MB"""
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except:
        return 0.0


def open_file_location(file_path: Path) -> bool:
    """
    Open file location in system file manager
    
    Args:
        file_path: Path to file or directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        system = platform.system().lower()
        
        if system == "windows":
            # Windows Explorer - select the file
            subprocess.run(["explorer", "/select,", str(file_path)], check=False)
        elif system == "darwin":
            # macOS Finder - select the file
            subprocess.run(["open", "-R", str(file_path)], check=False)
        elif system == "linux":
            # Linux file managers
            parent_dir = file_path.parent if file_path.is_file() else file_path
            try:
                # Try common file managers
                subprocess.run(["xdg-open", str(parent_dir)], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.run(["nautilus", str(parent_dir)], check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        subprocess.run(["dolphin", str(parent_dir)], check=True)
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        return False
        else:
            return False
            
        return True
    except Exception as e:
        print(f"Failed to open file location: {e}")
        return False


def get_tutorial_file_info(tutorial_id: str, storage) -> dict:
    """
    Get comprehensive file information for a tutorial
    
    Args:
        tutorial_id: Tutorial ID
        storage: TutorialStorage instance
        
    Returns:
        Dictionary with file information
    """
    project_path = storage.get_project_path(tutorial_id)
    if not project_path or not project_path.exists():
        return {"exists": False}
    
    info = {
        "exists": True,
        "project_path": str(project_path),
        "project_path_display": str(project_path).replace(str(Path.home()), "~"),
        "files": {}
    }
    
    # Check for exported files
    output_dir = project_path / "output"
    if output_dir.exists():
        # Load metadata to get the tutorial title for filename matching
        from ..core.storage import TutorialStorage
        temp_storage = storage if hasattr(storage, 'load_tutorial_metadata') else TutorialStorage()
        metadata = temp_storage.load_tutorial_metadata(tutorial_id)
        safe_title = sanitize_filename(metadata.title if metadata else "untitled")
        
        export_files = {
            "html": output_dir / f"{safe_title}.html",
            "word": output_dir / f"{safe_title}.docx", 
            "pdf": output_dir / f"{safe_title}.pdf"
        }
        
        # Fallback to legacy filenames if new ones don't exist
        if not (output_dir / f"{safe_title}.html").exists():
            legacy_files = {
                "html": output_dir / "index.html",
                "word": output_dir / "tutorial.docx", 
                "pdf": output_dir / "tutorial.pdf"
            }
            # Use legacy files if they exist
            for format_name, legacy_path in legacy_files.items():
                if legacy_path.exists():
                    export_files[format_name] = legacy_path
        
        for format_name, file_path in export_files.items():
            if file_path.exists():
                info["files"][format_name] = {
                    "path": str(file_path),
                    "size_mb": get_file_size_mb(file_path),
                    "exists": True
                }
            else:
                info["files"][format_name] = {"exists": False}
    
    # Check for screenshots
    screenshots_dir = project_path / "screenshots"
    if screenshots_dir.exists():
        screenshot_files = list(screenshots_dir.glob("*.png"))
        info["screenshot_count"] = len(screenshot_files)
    else:
        info["screenshot_count"] = 0
    
    return info


def generate_file_location_html(tutorial_id: str, storage, base_url: str = "") -> str:
    """
    Generate HTML for displaying file locations with click-to-open functionality
    
    Args:
        tutorial_id: Tutorial ID
        storage: TutorialStorage instance  
        base_url: Base URL for web interface
        
    Returns:
        HTML string
    """
    file_info = get_tutorial_file_info(tutorial_id, storage)
    
    if not file_info["exists"]:
        return '<span class="text-muted">No files found</span>'
    
    html = f"""
    <div class="file-locations">
        <div class="project-path">
            <strong>📁 Location:</strong> 
            <code class="clickable-path" onclick="openFileLocation('{tutorial_id}', 'project')" 
                  title="Click to open in file manager">
                {file_info['project_path_display']}
            </code>
        </div>
    """
    
    if file_info["files"]:
        html += '<div class="exported-files" style="margin-top: 8px;"><strong>📄 Exports:</strong><br>'
        
        for format_name, file_data in file_info["files"].items():
            if file_data.get("exists", False):
                size_info = f" ({file_data['size_mb']:.1f}MB)" if file_data['size_mb'] > 0 else ""
                html += f"""
                    <span class="file-link">
                        <a href="#" onclick="openFileLocation('{tutorial_id}', '{format_name}')" 
                           title="Click to open file location">
                            {format_name.upper()}{size_info}
                        </a>
                    </span>
                """
            else:
                html += f'<span class="file-missing text-muted">{format_name.upper()}</span>'
        
        html += '</div>'
    
    if file_info.get("screenshot_count", 0) > 0:
        html += f'<div style="margin-top: 5px;"><small class="text-muted">📷 {file_info["screenshot_count"]} screenshots</small></div>'
    
    html += '</div>'
    
    return html