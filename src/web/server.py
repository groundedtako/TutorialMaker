"""
Flask web server for tutorial editing interface
Local-only server for post-capture editing and management
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import webbrowser
import threading
import time
from datetime import datetime
import logging

from ..core.storage import TutorialStorage, TutorialMetadata, TutorialStep
from ..core.exporters import TutorialExporter
from ..utils.file_utils import open_file_location, get_tutorial_file_info
from .route_helpers import (
    load_and_validate_tutorial, render_tutorial_page, handle_tutorial_error,
    update_tutorial_metadata, update_tutorial_steps, delete_tutorial_step,
    format_export_results
)
from ..utils.api_utils import (
    success_response, error_response, handle_api_exception, APIException,
    require_fields, validate_tutorial_id
)

# No development mode imports - removed for stability

class TutorialWebServer:
    """Web server for tutorial editing and management"""
    
    def __init__(self, storage: TutorialStorage, port: int = 5000):
        self.storage = storage
        self.exporter = TutorialExporter(storage)
        self.port = port
        self.app_instance = None  # Reference to main app instance for session status
        
        # Create Flask app
        self.app = Flask(__name__, 
                        template_folder=str(Path(__file__).parent / "templates"),
                        static_folder=str(Path(__file__).parent / "static"))
        CORS(self.app)  # Enable CORS for localhost development

        # Configure logging to skip status endpoint
        class StatusEndpointFilter(logging.Filter):
            def filter(self, record):
                return 'GET /api/recording/status' not in record.getMessage()

        logging.getLogger('werkzeug').addFilter(StatusEndpointFilter())
        
        # Set up template filters
        self._setup_template_filters()
        
        # Set up routes
        self._setup_routes()
        
        # Server state
        self.server_thread = None
        self.running = False
    
    def _setup_template_filters(self):
        """Set up Jinja2 template filters"""
        @self.app.template_filter('timestamp_to_date')
        def timestamp_to_date(timestamp):
            try:
                if timestamp is None or timestamp == 0:
                    return "Unknown date"
                return datetime.fromtimestamp(timestamp).strftime('%B %d, %Y at %I:%M %p')
            except (ValueError, TypeError, OSError):
                return "Invalid date"
    
    def _setup_routes(self):
        """Set up Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main page - list all tutorials"""
            tutorials = self.storage.list_tutorials()
            return render_template('index.html', tutorials=tutorials)
        
        @self.app.route('/tutorial/<tutorial_id>')
        def view_tutorial(tutorial_id: str):
            """View/edit specific tutorial"""
            try:
                validate_tutorial_id(tutorial_id)
                metadata, steps = load_and_validate_tutorial(self.storage, tutorial_id)
                
                # Log successful load
                print(f"SUCCESS loading tutorial {tutorial_id}: {metadata.title} ({len(steps)} steps)")
                
                return render_tutorial_page(metadata, steps, tutorial_id)
                
            except APIException as e:
                return handle_tutorial_error(tutorial_id, e)
            except Exception as e:
                return handle_tutorial_error(tutorial_id, e)
        
        @self.app.route('/api/tutorials')
        def api_list_tutorials():
            """API: List all tutorials"""
            tutorials = self.storage.list_tutorials()
            return jsonify([{
                'tutorial_id': t.tutorial_id,
                'title': t.title,
                'description': t.description,
                'created_at': t.created_at,
                'step_count': t.step_count,
                'duration': t.duration,
                'status': t.status
            } for t in tutorials])
        
        @self.app.route('/api/tutorial/<tutorial_id>')
        def api_get_tutorial(tutorial_id: str):
            """API: Get tutorial data"""
            metadata = self.storage.load_tutorial_metadata(tutorial_id)
            steps = self.storage.load_tutorial_steps(tutorial_id)
            
            if not metadata or steps is None:
                return jsonify({'error': 'Tutorial not found'}), 404
            
            return jsonify({
                'metadata': {
                    'tutorial_id': metadata.tutorial_id,
                    'title': metadata.title,
                    'description': metadata.description,
                    'created_at': metadata.created_at,
                    'last_modified': metadata.last_modified,
                    'duration': metadata.duration,
                    'step_count': metadata.step_count,
                    'status': metadata.status,
                    'tags': metadata.tags
                },
                'steps': [{
                    'step_id': s.step_id,
                    'step_number': s.step_number,
                    'description': s.description,
                    'screenshot_path': s.screenshot_path,
                    'coordinates': s.coordinates,
                    'ocr_confidence': s.ocr_confidence,
                    'step_type': s.step_type
                } for s in steps]
            })
        
        @self.app.route('/api/tutorial/<tutorial_id>/update', methods=['POST'])
        def api_update_tutorial(tutorial_id: str):
            """API: Update tutorial metadata and steps"""
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Update metadata if provided
            if 'metadata' in data:
                metadata = self.storage.load_tutorial_metadata(tutorial_id)
                if not metadata:
                    return jsonify({'error': 'Tutorial not found'}), 404
                
                # Update fields
                metadata_updates = data['metadata']
                if 'title' in metadata_updates:
                    metadata.title = metadata_updates['title']
                if 'description' in metadata_updates:
                    metadata.description = metadata_updates['description']
                if 'tags' in metadata_updates:
                    metadata.tags = metadata_updates['tags']
                
                metadata.last_modified = time.time()
                
                # Save updated metadata
                project_path = self.storage.get_project_path(tutorial_id)
                if project_path:
                    self.storage._save_metadata(project_path, metadata)
            
            # Update steps if provided
            if 'steps' in data:
                steps = self.storage.load_tutorial_steps(tutorial_id)
                if steps is None:
                    return jsonify({'error': 'Tutorial not found'}), 404
                
                steps_updates = {s['step_id']: s for s in data['steps']}
                
                # Update step descriptions
                for step in steps:
                    if step.step_id in steps_updates:
                        update = steps_updates[step.step_id]
                        if 'description' in update:
                            step.description = update['description']
                
                # Save updated steps
                project_path = self.storage.get_project_path(tutorial_id)
                if project_path:
                    self.storage._save_steps(project_path, steps)
            
            return jsonify({'success': True})
        
        @self.app.route('/api/tutorial/<tutorial_id>/delete_step', methods=['POST'])
        def api_delete_step(tutorial_id: str):
            """API: Delete a tutorial step"""
            data = request.get_json()
            step_id = data.get('step_id')
            
            if not step_id:
                return jsonify({'error': 'step_id required'}), 400
            
            steps = self.storage.load_tutorial_steps(tutorial_id)
            if steps is None:
                return jsonify({'error': 'Tutorial not found'}), 404
            
            # Remove step
            steps = [s for s in steps if s.step_id != step_id]
            
            # Renumber remaining steps
            for i, step in enumerate(steps, 1):
                step.step_number = i
            
            # Save updated steps
            project_path = self.storage.get_project_path(tutorial_id)
            if project_path:
                self.storage._save_steps(project_path, steps)
                
                # Update metadata step count
                metadata = self.storage.load_tutorial_metadata(tutorial_id)
                if metadata:
                    metadata.step_count = len(steps)
                    metadata.last_modified = time.time()
                    self.storage._save_metadata(project_path, metadata)
            
            return jsonify({'success': True, 'new_step_count': len(steps)})
        
        @self.app.route('/api/tutorial/<tutorial_id>/export', methods=['POST'])
        def api_export_tutorial(tutorial_id: str):
            """API: Export tutorial to specified formats"""
            data = request.get_json()
            formats = data.get('formats', ['html', 'word', 'pdf'])
            
            try:
                results = self.exporter.export_tutorial(tutorial_id, formats)
                return jsonify({
                    'success': True,
                    'results': results
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/tutorial/<tutorial_id>/files')
        def api_get_tutorial_files(tutorial_id: str):
            """API: Get tutorial file information"""
            try:
                file_info = get_tutorial_file_info(tutorial_id, self.storage)
                return jsonify(file_info)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/tutorial/<tutorial_id>/open_location', methods=['POST'])
        def api_open_file_location(tutorial_id: str):
            """API: Open tutorial file location in system file manager"""
            try:
                data = request.get_json() or {}
                file_type = data.get('file_type', 'project')  # project, html, word, pdf
                
                project_path = self.storage.get_project_path(tutorial_id)
                if not project_path:
                    return jsonify({'error': 'Tutorial not found'}), 404
                
                if file_type == 'project':
                    target_path = project_path
                else:
                    # Open specific exported file
                    output_dir = project_path / "output"
                    
                    # Load metadata to get the tutorial title for filename matching
                    metadata = self.storage.load_tutorial_metadata(tutorial_id)
                    from ..utils.file_utils import sanitize_filename
                    safe_title = sanitize_filename(metadata.title if metadata else "untitled")
                    
                    file_map = {
                        'html': output_dir / f"{safe_title}.html",
                        'word': output_dir / f"{safe_title}.docx",
                        'pdf': output_dir / f"{safe_title}.pdf"
                    }
                    
                    # Fallback to legacy filenames
                    if file_type in file_map and not file_map[file_type].exists():
                        legacy_map = {
                            'html': output_dir / "index.html",
                            'word': output_dir / "tutorial.docx",
                            'pdf': output_dir / "tutorial.pdf"
                        }
                        if file_type in legacy_map and legacy_map[file_type].exists():
                            file_map[file_type] = legacy_map[file_type]
                    
                    if file_type not in file_map:
                        return jsonify({'error': f'Unknown file type: {file_type}'}), 400
                    
                    target_path = file_map[file_type]
                    if not target_path.exists():
                        return jsonify({'error': f'{file_type.upper()} file not found. Export first.'}), 404
                
                success = open_file_location(target_path)
                return jsonify({
                    'success': success,
                    'message': f'Opened {file_type} location' if success else 'Failed to open file location'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        
        @self.app.route('/api/tutorial/<tutorial_id>/delete', methods=['POST'])
        def api_delete_tutorial(tutorial_id: str):
            """API: Delete entire tutorial"""
            success = self.storage.delete_tutorial(tutorial_id)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Failed to delete tutorial'}), 500
        
        @self.app.route('/api/tutorials/delete_all', methods=['POST'])
        def api_delete_all_tutorials():
            """API: Delete all tutorials"""
            try:
                results = self.storage.delete_all_tutorials()
                success_count = sum(1 for success in results.values() if success)
                total_count = len(results)
                
                return jsonify({
                    'success': True,
                    'results': results,
                    'summary': {
                        'total': total_count,
                        'deleted': success_count,
                        'failed': total_count - success_count
                    }
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/tutorials/export_all', methods=['POST'])
        def api_export_all_tutorials():
            """API: Export all tutorials to specified formats"""
            try:
                data = request.get_json() or {}
                formats = data.get('formats', ['html', 'word'])
                max_workers = data.get('max_workers', 3)
                
                results = self.exporter.export_all_tutorials(formats, max_workers)
                
                # Calculate summary statistics
                total_tutorials = len(results)
                successful_exports = 0
                failed_exports = 0
                
                for tutorial_results in results.values():
                    if isinstance(tutorial_results, dict) and 'error' not in tutorial_results:
                        successful_exports += 1
                    else:
                        failed_exports += 1
                
                return jsonify({
                    'success': True,
                    'results': results,
                    'summary': {
                        'total_tutorials': total_tutorials,
                        'successful': successful_exports,
                        'failed': failed_exports,
                        'formats': formats
                    }
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/screenshots/<tutorial_id>/<filename>')
        def serve_screenshot(tutorial_id: str, filename: str):
            """Serve screenshot files"""
            project_path = self.storage.get_project_path(tutorial_id)
            if not project_path:
                return jsonify({'error': 'Tutorial not found'}), 404
            
            screenshots_dir = project_path / "screenshots"
            return send_from_directory(screenshots_dir, filename)
        
        @self.app.route('/download/<tutorial_id>/<filename>')
        def download_file(tutorial_id: str, filename: str):
            """Download exported files"""
            project_path = self.storage.get_project_path(tutorial_id)
            if not project_path:
                return jsonify({'error': 'Tutorial not found'}), 404
            
            output_dir = project_path / "output"
            file_path = output_dir / filename
            
            if not file_path.exists():
                return jsonify({'error': 'File not found'}), 404
            
            return send_file(file_path, as_attachment=True)
        
        @self.app.route('/api/recording/status')
        def api_recording_status():
            """API: Get current recording session status"""
            if not self.app_instance:
                return jsonify({
                    'status': 'no_session',
                    'message': 'No app instance connected'
                })
            
            status = self.app_instance.get_current_session_status()
            return jsonify(status)
        
        @self.app.route('/api/recording/new', methods=['POST'])
        def api_new_recording():
            """API: Create new recording session"""
            print(f"DEBUG: api_new_recording called")
            
            if not self.app_instance:
                print(f"ERROR: No app instance connected")
                return jsonify({'error': 'No app instance connected'}), 500
            
            data = request.get_json()
            title = data.get('title', '') if data else ''
            description = data.get('description', '') if data else ''
            
            print(f"DEBUG: Creating tutorial with title='{title}', description='{description}'")

            try:
                tutorial_id = self.app_instance.new_tutorial(title, description)
                print(f"DEBUG: Successfully created tutorial with ID: {tutorial_id}")
                return jsonify({
                    'success': True,
                    'tutorial_id': tutorial_id
                })
            except Exception as e:
                print(f"ERROR: Failed to create tutorial: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recording/start', methods=['POST'])
        def api_start_recording():
            """API: Start recording"""
            if not self.app_instance:
                return jsonify({'error': 'No app instance connected'}), 500
            
            try:
                success = self.app_instance.start_recording()
                if success:
                    return jsonify({'success': True})
                else:
                    return jsonify({'error': 'Failed to start recording'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recording/pause', methods=['POST'])
        def api_pause_recording():
            """API: Pause recording"""
            if not self.app_instance:
                return jsonify({'error': 'No app instance connected'}), 500
            
            try:
                self.app_instance.pause_recording()
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recording/resume', methods=['POST'])
        def api_resume_recording():
            """API: Resume recording"""
            if not self.app_instance:
                return jsonify({'error': 'No app instance connected'}), 500
            
            try:
                self.app_instance.resume_recording()
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recording/stop', methods=['POST'])
        def api_stop_recording():
            """API: Stop recording"""
            if not self.app_instance:
                return jsonify({'error': 'No app instance connected'}), 500
            
            try:
                tutorial_id = self.app_instance.stop_recording()
                if tutorial_id:
                    return jsonify({
                        'success': True,
                        'tutorial_id': tutorial_id
                    })
                else:
                    return jsonify({'error': 'No active recording session'}), 400
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recording/toggle-keystroke-filter', methods=['POST'])
        def api_toggle_keystroke_filter():
            """API: Toggle keystroke filtering on/off"""
            try:
                if self.app_instance:
                    enabled = self.app_instance.toggle_keystroke_filtering()
                    return jsonify({
                        'success': True,
                        'enabled': enabled
                    })
                else:
                    return jsonify({'error': 'App not available'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recording/monitors')
        def api_get_monitors():
            """API: Get available monitors for selection"""
            try:
                if self.app_instance:
                    screen_info = self.app_instance.screen_capture.get_screen_info()
                    monitors = screen_info.get('monitors', [])
                    
                    # Generate thumbnails for each monitor
                    monitor_data = []
                    for monitor in monitors:
                        try:
                            # Capture small thumbnail
                            screenshot = self.app_instance.screen_capture.capture_full_screen(monitor_id=monitor['id'])
                            if screenshot:
                                # Create small thumbnail for web display
                                from PIL import Image
                                import base64
                                import io
                                
                                # Resize to small thumbnail
                                thumbnail_size = (200, 150)
                                img_width, img_height = screenshot.size
                                scale = min(thumbnail_size[0] / img_width, thumbnail_size[1] / img_height)
                                new_size = (int(img_width * scale), int(img_height * scale))
                                
                                thumbnail = screenshot.resize(new_size, Image.Resampling.LANCZOS)
                                
                                # Convert to base64 for web display
                                buffer = io.BytesIO()
                                thumbnail.save(buffer, format='PNG')
                                img_data = base64.b64encode(buffer.getvalue()).decode()
                                
                                monitor_data.append({
                                    'id': monitor['id'],
                                    'width': monitor['width'],
                                    'height': monitor['height'],
                                    'left': monitor['left'],
                                    'top': monitor['top'],
                                    'thumbnail': f"data:image/png;base64,{img_data}"
                                })
                        except Exception as e:
                            print(f"Failed to capture monitor {monitor['id']}: {e}")
                            # Add monitor without thumbnail
                            monitor_data.append({
                                'id': monitor['id'],
                                'width': monitor['width'],
                                'height': monitor['height'],
                                'left': monitor['left'],
                                'top': monitor['top'],
                                'thumbnail': None
                            })
                    
                    return jsonify({
                        'success': True,
                        'monitors': monitor_data
                    })
                else:
                    return jsonify({'error': 'App not available'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/recording/select-monitor', methods=['POST'])
        def api_select_monitor():
            """API: Set selected monitor for recording"""
            try:
                data = request.get_json()
                monitor_id = data.get('monitor_id')
                
                if monitor_id is None:
                    return jsonify({'error': 'monitor_id required'}), 400
                
                if self.app_instance:
                    # Store selected monitor for next tutorial creation
                    self.app_instance.selected_monitor_id = int(monitor_id)
                    return jsonify({
                        'success': True,
                        'selected_monitor': monitor_id
                    })
                else:
                    return jsonify({'error': 'App not available'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def start(self, open_browser: bool = True) -> str:
        """
        Start the web server
        
        Args:
            open_browser: Whether to open browser automatically
            
        Returns:
            Server URL
        """
        if self.running:
            return f"http://localhost:{self.port}"
        
        def run_server():
            self.app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.running = True
        
        # Wait a moment for server to start
        time.sleep(1)
        
        url = f"http://localhost:{self.port}"
        
        if open_browser:
            webbrowser.open(url)
        
        print(f"Tutorial web server started at {url}")
        return url
    
    def stop(self):
        """Stop the web server"""
        self.running = False
        # Note: Flask development server doesn't have a clean shutdown method
        # In production, you'd use a proper WSGI server like Gunicorn
    
    def get_url(self) -> Optional[str]:
        """Get server URL if running"""
        if self.running:
            return f"http://localhost:{self.port}"
        return None
    
    def set_app_instance(self, app_instance):
        """Set reference to main app instance for session status"""
        self.app_instance = app_instance
    
