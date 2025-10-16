"""
Event storage and tutorial data management
Local file-based storage for captured events and tutorial data
"""

import os
import json
import uuid
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available. Screenshot processing may be limited.")

from .events import MouseClickEvent, KeyPressEvent, TextInputEvent, EventType
from .logger import get_logger

@dataclass
class TutorialStep:
    """A single step in a tutorial"""
    step_id: str
    timestamp: float
    step_number: int
    description: str
    screenshot_path: Optional[str] = None
    event_data: Optional[Dict] = None
    ocr_text: Optional[str] = None
    ocr_confidence: float = 0.0
    coordinates: Optional[tuple] = None
    coordinates_pct: Optional[tuple] = None  # (x_pct, y_pct) as floats 0.0-1.0
    screen_dimensions: Optional[tuple] = None  # (width, height) at time of capture
    step_type: str = "click"  # click, type, special

@dataclass
class TutorialMetadata:
    """Metadata for a tutorial project"""
    tutorial_id: str
    title: str
    description: str
    created_at: float
    last_modified: float
    duration: float
    step_count: int
    applications_used: List[str]
    status: str  # recording, paused, completed
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class TutorialStorage:
    """Manages storage of tutorial data and projects"""
    
    def __init__(self, base_path: Optional[Path] = None):
        # Set up base directory
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path.home() / "TutorialMaker"
        
        # Create directory structure
        self.projects_path = self.base_path / "projects"
        self.templates_path = self.base_path / "templates"
        self.temp_path = self.base_path / "temp"
        self.logger = get_logger('core.storage')
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for path in [self.base_path, self.projects_path, self.templates_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def create_tutorial_project(self, title: str = None, description: str = "") -> str:
        """
        Create a new tutorial project
        
        Args:
            title: Optional title for the tutorial
            description: Optional description
            
        Returns:
            Tutorial ID (UUID string)
        """
        tutorial_id = str(uuid.uuid4())
        
        # Generate title if not provided
        if not title:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            title = f"Tutorial_{timestamp}"
        
        # Create project directory
        project_path = self.projects_path / f"tutorial_{tutorial_id[:8]}"
        project_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (project_path / "screenshots").mkdir(exist_ok=True)
        (project_path / "output").mkdir(exist_ok=True)
        
        # Create metadata
        metadata = TutorialMetadata(
            tutorial_id=tutorial_id,
            title=title,
            description=description,
            created_at=time.time(),
            last_modified=time.time(),
            duration=0.0,
            step_count=0,
            applications_used=[],
            status="recording"
        )
        
        # Save metadata
        self._save_metadata(project_path, metadata)
        
        # Initialize empty events file
        self._save_events(project_path, [])
        
        return tutorial_id
    
    def get_project_path(self, tutorial_id: str) -> Optional[Path]:
        """Get the path to a tutorial project"""
        # Find project directory (search by ID prefix)
        for project_dir in self.projects_path.iterdir():
            if project_dir.is_dir() and tutorial_id[:8] in project_dir.name:
                return project_dir
        return None
    
    def save_tutorial_step(self, tutorial_id: str, step: TutorialStep) -> bool:
        """
        Save a tutorial step
        
        Args:
            tutorial_id: Tutorial ID
            step: TutorialStep to save
            
        Returns:
            True if saved successfully
        """
        project_path = self.get_project_path(tutorial_id)
        if not project_path:
            self.logger.error(f"Project not found: {tutorial_id}")
            return False
        
        try:
            # Load existing steps
            steps = self.load_tutorial_steps(tutorial_id) or []
            
            # Add new step
            steps.append(step)
            
            # Save steps
            self._save_steps(project_path, steps)
            
            # Update metadata
            metadata = self.load_tutorial_metadata(tutorial_id)
            if metadata:
                metadata.step_count = len(steps)
                metadata.last_modified = time.time()
                self._save_metadata(project_path, metadata)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving tutorial step: {e}")
            return False
    
    def load_tutorial_steps(self, tutorial_id: str) -> Optional[List[TutorialStep]]:
        """Load all steps for a tutorial"""
        project_path = self.get_project_path(tutorial_id)
        if not project_path:
            return None
        
        steps_file = project_path / "steps.json"
        if not steps_file.exists():
            return []
        
        try:
            with open(steps_file, 'r') as f:
                steps_data = json.load(f)
            
            steps = []
            for step_data in steps_data:
                # Convert coordinates back to tuple if it exists
                if 'coordinates' in step_data and step_data['coordinates']:
                    step_data['coordinates'] = tuple(step_data['coordinates'])
                
                # Convert percentage coordinates back to tuple if it exists
                if 'coordinates_pct' in step_data and step_data['coordinates_pct']:
                    step_data['coordinates_pct'] = tuple(step_data['coordinates_pct'])
                
                # Convert screen dimensions back to tuple if it exists
                if 'screen_dimensions' in step_data and step_data['screen_dimensions']:
                    step_data['screen_dimensions'] = tuple(step_data['screen_dimensions'])
                
                step = TutorialStep(**step_data)
                steps.append(step)
            
            return steps
            
        except Exception as e:
            self.logger.error(f"Error loading tutorial steps: {e}")
            return None
    
    def load_tutorial_metadata(self, tutorial_id: str) -> Optional[TutorialMetadata]:
        """Load metadata for a tutorial"""
        project_path = self.get_project_path(tutorial_id)
        if not project_path:
            return None
        
        metadata_file = project_path / "metadata.json"
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r') as f:
                metadata_data = json.load(f)
            
            return TutorialMetadata(**metadata_data)
            
        except Exception as e:
            self.logger.error(f"Error loading tutorial metadata: {e}")
            return None
    
    def save_screenshot(self, tutorial_id: str, image, step_number: int) -> Optional[str]:
        """
        Save a screenshot for a tutorial step
        
        Args:
            tutorial_id: Tutorial ID
            image: PIL Image to save
            step_number: Step number for filename
            
        Returns:
            Relative path to saved screenshot or None if failed
        """
        project_path = self.get_project_path(tutorial_id)
        if not project_path:
            return None
        
        try:
            # Get tutorial metadata for naming
            metadata = self.load_tutorial_metadata(tutorial_id)
            tutorial_name = "untitled"
            if metadata and metadata.title:
                # Sanitize title for filename
                tutorial_name = "".join(c for c in metadata.title.lower() if c.isalnum() or c in (' ', '-', '_')).strip()
                tutorial_name = tutorial_name.replace(' ', '_')
                if len(tutorial_name) > 20:
                    tutorial_name = tutorial_name[:20]
            
            screenshots_dir = project_path / "screenshots"
            # Include tutorial name and hash in filename: tutorialname_abcd1234_step_001.jpg
            tutorial_hash = tutorial_id.replace('-', '')[:8]  # First 8 chars without hyphens
            screenshot_filename = f"{tutorial_name}_{tutorial_hash}_step_{step_number:03d}.jpg"
            screenshot_path = screenshots_dir / screenshot_filename
            
            # Save image as JPEG for faster saving and smaller file size
            # Convert RGBA to RGB if needed (JPEG doesn't support transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = rgb_image
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save as optimized JPEG (quality=85 is good balance of size vs quality)
            image.save(screenshot_path, "JPEG", quality=85, optimize=True)
            
            # Return relative path
            return f"screenshots/{screenshot_filename}"
            
        except Exception as e:
            self.logger.error(f"Error saving screenshot: {e}")
            return None
    
    def list_tutorials_lite(self) -> List[Dict[str, Any]]:
        """List all tutorials with minimal data (for fast loading)"""
        tutorials = []

        try:
            for project_dir in self.projects_path.iterdir():
                if project_dir.is_dir():
                    metadata_file = project_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata_data = json.load(f)
                            # Only include essential fields for listing
                            tutorials.append({
                                'tutorial_id': metadata_data.get('tutorial_id'),
                                'title': metadata_data.get('title', 'Untitled'),
                                'created_at': metadata_data.get('created_at', 0),
                                'step_count': metadata_data.get('step_count', 0)
                            })
                        except Exception as e:
                            self.logger.warning(f"Error loading metadata for {project_dir}: {e}")

            # Sort by creation date (newest first)
            tutorials.sort(key=lambda x: x['created_at'], reverse=True)

        except Exception as e:
            self.logger.error(f"Error listing tutorials: {e}")

        return tutorials

    def list_tutorials(self) -> List[TutorialMetadata]:
        """List all available tutorials (full metadata)"""
        tutorials = []

        try:
            for project_dir in self.projects_path.iterdir():
                if project_dir.is_dir():
                    metadata_file = project_dir / "metadata.json"
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata_data = json.load(f)
                            metadata = TutorialMetadata(**metadata_data)
                            tutorials.append(metadata)
                        except Exception as e:
                            self.logger.warning(f"Error loading metadata for {project_dir}: {e}")

            # Sort by creation date (newest first)
            tutorials.sort(key=lambda x: x.created_at, reverse=True)

        except Exception as e:
            self.logger.error(f"Error listing tutorials: {e}")

        return tutorials
    
    def delete_tutorial(self, tutorial_id: str) -> bool:
        """Delete a tutorial project completely"""
        project_path = self.get_project_path(tutorial_id)
        if not project_path:
            return False
        
        try:
            shutil.rmtree(project_path)
            return True
        except Exception as e:
            self.logger.error(f"Error deleting tutorial: {e}")
            return False
    
    def delete_all_tutorials(self) -> Dict[str, bool]:
        """
        Delete all tutorials
        
        Returns:
            Dictionary mapping tutorial IDs to success status
        """
        tutorials = self.list_tutorials()
        results = {}
        
        for tutorial in tutorials:
            try:
                success = self.delete_tutorial(tutorial.tutorial_id)
                results[tutorial.tutorial_id] = success
                if success:
                    self.logger.info(f"Deleted tutorial: {tutorial.title} ({tutorial.tutorial_id})")
                else:
                    self.logger.warning(f"Failed to delete tutorial: {tutorial.title} ({tutorial.tutorial_id})")
            except Exception as e:
                self.logger.error(f"Error deleting tutorial {tutorial.tutorial_id}: {e}")
                results[tutorial.tutorial_id] = False
        
        return results
    
    def update_tutorial_status(self, tutorial_id: str, status: str) -> bool:
        """Update tutorial status (recording, paused, completed)"""
        metadata = self.load_tutorial_metadata(tutorial_id)
        if not metadata:
            return False
        
        metadata.status = status
        metadata.last_modified = time.time()
        
        project_path = self.get_project_path(tutorial_id)
        if project_path:
            return self._save_metadata(project_path, metadata)
        
        return False
    
    def _save_metadata(self, project_path: Path, metadata: TutorialMetadata) -> bool:
        """Save metadata to project directory"""
        try:
            metadata_file = project_path / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")
            return False
    
    def _save_steps(self, project_path: Path, steps: List[TutorialStep]) -> bool:
        """Save steps to project directory"""
        try:
            steps_file = project_path / "steps.json"
            steps_data = []
            
            for step in steps:
                step_dict = asdict(step)
                # Convert tuple coordinates to list for JSON serialization
                if step_dict.get('coordinates'):
                    step_dict['coordinates'] = list(step_dict['coordinates'])
                
                # Convert tuple percentage coordinates to list for JSON serialization
                if step_dict.get('coordinates_pct'):
                    step_dict['coordinates_pct'] = list(step_dict['coordinates_pct'])
                
                # Convert tuple screen dimensions to list for JSON serialization
                if step_dict.get('screen_dimensions'):
                    step_dict['screen_dimensions'] = list(step_dict['screen_dimensions'])
                
                steps_data.append(step_dict)
            
            with open(steps_file, 'w') as f:
                json.dump(steps_data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving steps: {e}")
            return False
    
    def _save_events(self, project_path: Path, events: List) -> bool:
        """Save raw events to project directory (for debugging/analysis)"""
        try:
            events_file = project_path / "events.json"
            with open(events_file, 'w') as f:
                json.dump(events, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving events: {e}")
            return False
    
    def export_tutorial_data(self, tutorial_id: str) -> Optional[Dict]:
        """Export complete tutorial data for sharing/backup"""
        metadata = self.load_tutorial_metadata(tutorial_id)
        steps = self.load_tutorial_steps(tutorial_id)
        
        if not metadata or not steps:
            return None
        
        return {
            'metadata': asdict(metadata),
            'steps': [asdict(step) for step in steps],
            'export_timestamp': time.time(),
            'version': '1.0'
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            total_tutorials = len(list(self.projects_path.iterdir()))
            
            # Calculate total size
            total_size = 0
            for project_dir in self.projects_path.rglob('*'):
                if project_dir.is_file():
                    total_size += project_dir.stat().st_size
            
            return {
                'base_path': str(self.base_path),
                'total_tutorials': total_tutorials,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'directories_exist': all(p.exists() for p in [self.projects_path, self.templates_path, self.temp_path])
            }
        except Exception as e:
            self.logger.error(f"Error getting storage stats: {e}")
            return {'error': str(e)}