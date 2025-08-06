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

from ..core.storage import TutorialStorage, TutorialMetadata, TutorialStep
from ..core.exporters import TutorialExporter
from ..utils.file_utils import open_file_location, get_tutorial_file_info

# Development mode imports
try:
    from ..utils.dev_utils import live_reload_manager, inject_live_reload_script
    DEV_UTILS_AVAILABLE = True
except ImportError:
    DEV_UTILS_AVAILABLE = False

class TutorialWebServer:
    """Web server for tutorial editing and management"""
    
    def __init__(self, storage: TutorialStorage, port: int = 5000, dev_mode: bool = False):
        self.storage = storage
        self.exporter = TutorialExporter(storage)
        self.port = port
        self.app_instance = None  # Reference to main app instance for session status
        self.dev_mode = dev_mode  # Enable development features
        
        # Create Flask app
        self.app = Flask(__name__, 
                        template_folder=str(Path(__file__).parent / "templates"),
                        static_folder=str(Path(__file__).parent / "static"))
        CORS(self.app)  # Enable CORS for localhost development
        
        # Add development mode interceptor
        if self.dev_mode and DEV_UTILS_AVAILABLE:
            self._setup_dev_interceptor()
        
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
            html = render_template('index.html', tutorials=tutorials)
            
            # Inject live reload in development mode
            if self.dev_mode and DEV_UTILS_AVAILABLE:
                html = inject_live_reload_script(html)
                
            return html
        
        @self.app.route('/tutorial/<tutorial_id>')
        def view_tutorial(tutorial_id: str):
            """View/edit specific tutorial"""
            try:
                metadata = self.storage.load_tutorial_metadata(tutorial_id)
                steps = self.storage.load_tutorial_steps(tutorial_id)
                
                if not metadata:
                    return render_template('tutorial_not_found.html', tutorial_id=tutorial_id), 404
                
                if steps is None:
                    steps = []
                
                # Validate and clean step data
                validated_steps = []
                for i, step in enumerate(steps):
                    try:
                        # Check if step has required attributes
                        if not hasattr(step, 'step_id'):
                            print(f"Warning: Step {i} missing step_id")
                            continue
                        if not hasattr(step, 'description'):
                            print(f"Warning: Step {i} missing description")
                            continue
                        validated_steps.append(step)
                    except Exception as e:
                        print(f"Warning: Skipping malformed step {i}: {e}")
                        continue
                
                steps = validated_steps
                
                # Detailed success logging
                print(f"\nSUCCESS loading tutorial {tutorial_id}:")
                print(f"   Title: {metadata.title}")
                print(f"   Steps: {len(steps)}")
                print(f"   Created: {metadata.created_at}")
                print(f"   Duration: {metadata.duration}s")
                print(f"   Status: {metadata.status}")
                
                # Log step details for debugging
                if steps:
                    print(f"   Step details:")
                    for i, step in enumerate(steps[:3]):  # First 3 steps
                        print(f"      {i+1}. {step.description[:50]}...")
                        if hasattr(step, 'screenshot_path'):
                            print(f"         Screenshot: {step.screenshot_path}")
                        if hasattr(step, 'ocr_confidence'):
                            print(f"         OCR: {step.ocr_confidence}")
                    if len(steps) > 3:
                        print(f"      ... and {len(steps) - 3} more steps")
                
                print(f"   Template: tutorial.html")
                print(f"   URL: /tutorial/{tutorial_id}")
                print("   Rendering template...")
                
                return render_template('tutorial.html', 
                                     metadata=metadata, 
                                     steps=steps,
                                     tutorial_id=tutorial_id)
            except Exception as e:
                # Detailed error logging
                print(f"\nERROR in view_tutorial for {tutorial_id}:")
                print(f"   Error type: {type(e).__name__}")
                print(f"   Error message: {str(e)}")
                print(f"   Tutorial ID: {tutorial_id}")
                
                import traceback
                traceback.print_exc()
                
                # Try to load metadata to determine if tutorial exists
                try:
                    test_metadata = self.storage.load_tutorial_metadata(tutorial_id)
                    if test_metadata:
                        print(f"   Tutorial EXISTS: {test_metadata.title}")
                        error_msg = f"Template rendering error: {str(e)}"
                    else:
                        print(f"   Tutorial MISSING")
                        return render_template('tutorial_not_found.html', tutorial_id=tutorial_id), 404
                except Exception as e2:
                    print(f"   Storage error too: {e2}")
                    error_msg = f"Storage and template error: {str(e)}"
                
                # Return proper error page instead of JSON
                return render_template('tutorial_error.html', 
                                     tutorial_id=tutorial_id, 
                                     error_message=error_msg), 500
        
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
        
        @self.app.route('/api/dev/reload-check')
        def api_dev_reload_check():
            """API: Check if reload is needed (development mode)"""
            if not self.dev_mode or not DEV_UTILS_AVAILABLE:
                return jsonify({'error': 'Development mode not available'}), 404
            
            return jsonify({
                'timestamp': live_reload_manager.get_reload_timestamp(),
                'dev_mode': True
            })
        
        @self.app.route('/api/tutorial/<tutorial_id>/delete', methods=['POST'])
        def api_delete_tutorial(tutorial_id: str):
            """API: Delete entire tutorial"""
            success = self.storage.delete_tutorial(tutorial_id)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Failed to delete tutorial'}), 500
        
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
            if not self.app_instance:
                return jsonify({'error': 'No app instance connected'}), 500
            
            data = request.get_json()
            title = data.get('title', '') if data else ''
            description = data.get('description', '') if data else ''
            
            try:
                tutorial_id = self.app_instance.new_tutorial(title, description)
                return jsonify({
                    'success': True,
                    'tutorial_id': tutorial_id
                })
            except Exception as e:
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
    
    def _setup_dev_interceptor(self):
        """Set up development mode response interceptor"""
        @self.app.after_request
        def inject_live_reload(response):
            # Only inject into HTML responses
            if (response.content_type and 
                'text/html' in response.content_type and 
                response.status_code == 200):
                
                try:
                    html_content = response.get_data(as_text=True)
                    modified_html = inject_live_reload_script(html_content)
                    response.set_data(modified_html)
                except Exception as e:
                    print(f"Warning: Failed to inject live reload script: {e}")
                    
            return response