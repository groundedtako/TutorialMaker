"""
Event Processing Pipeline
Converts queued events into tutorial steps with OCR, coordinate mapping, and storage
"""

import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from .event_queue import QueuedEvent
from .events import MouseClickEvent, KeyPressEvent, ManualCaptureEvent, EventType
from .capture import ScreenCapture
from .ocr import OCREngine, OCRResult
from .smart_ocr import SmartOCRProcessor
from .storage import TutorialStorage, TutorialStep


class EventProcessor:
    """Processes queued events into tutorial steps"""
    
    def __init__(self, 
                 screen_capture: ScreenCapture,
                 ocr_engine: OCREngine,
                 smart_ocr: SmartOCRProcessor,
                 storage: TutorialStorage,
                 debug_mode: bool = False):
        self.screen_capture = screen_capture
        self.ocr_engine = ocr_engine
        self.smart_ocr = smart_ocr
        self.storage = storage
        self.debug_mode = debug_mode
    
    def process_events_to_steps(self, 
                               events: List[QueuedEvent], 
                               tutorial_id: str,
                               session) -> int:
        """
        Process a list of queued events into tutorial steps
        
        Args:
            events: List of QueuedEvent objects to process
            tutorial_id: Tutorial ID for storage
            session: Recording session object for step counter
            
        Returns:
            Number of steps created
        """
        if not events:
            print("No events to process")
            return 0
        
        print(f"EventProcessor: Processing {len(events)} events into tutorial steps...")
        steps_created = 0
        processed_step_number = 0  # Track processed steps separately from captured steps
        
        for queued_event in events:
            try:
                if queued_event.event_type == 'mouse_click':
                    processed_step_number += 1
                    if self._process_mouse_click_event(queued_event, tutorial_id, session, processed_step_number):
                        steps_created += 1
                elif queued_event.event_type == 'manual_capture':
                    processed_step_number += 1
                    if self._process_manual_capture_event(queued_event, tutorial_id, session, processed_step_number):
                        steps_created += 1
                elif queued_event.event_type == 'keyboard_event':
                    processed_step_number += 1
                    if self._process_keyboard_event(queued_event, tutorial_id, session, processed_step_number):
                        steps_created += 1
            except Exception as e:
                print(f"EventProcessor: Error processing {queued_event.event_type} event: {e}")
        
        print(f"EventProcessor: Created {steps_created} tutorial steps from {len(events)} events")
        return steps_created
    
    def _process_mouse_click_event(self, queued_event: QueuedEvent, tutorial_id: str, session, step_number: int) -> bool:
        """Process a queued mouse click event into a tutorial step"""
        event = queued_event.event_object
        screenshot = queued_event.screenshot
        
        if not screenshot:
            print("EventProcessor: No screenshot available for click event")
            return False
        
        try:
            # Use pre-calculated coordinate info if available
            if queued_event.coordinate_info:
                coord_info = queued_event.coordinate_info
                screen_width = coord_info['screen_width']
                screen_height = coord_info['screen_height']
                monitor_relative_x = coord_info['monitor_relative_x']
                monitor_relative_y = coord_info['monitor_relative_y']
                monitor_info = coord_info['monitor_info']
                
                # Calculate percentage coordinates relative to the captured monitor
                if monitor_info:
                    x_pct = monitor_relative_x / monitor_info['width']
                    y_pct = monitor_relative_y / monitor_info['height']
                else:
                    x_pct = event.x / screen_width
                    y_pct = event.y / screen_height
                
                # Screenshot coordinates are the monitor-relative coordinates
                screenshot_click_x = monitor_relative_x
                screenshot_click_y = monitor_relative_y
            else:
                # Fallback to basic calculation if coordinate info not available
                print("EventProcessor: Warning - No coordinate info available, using fallback calculation")
                screen_info = self.screen_capture.get_screen_info()
                screen_width = screen_info['width']
                screen_height = screen_info['height']
                x_pct = event.x / screen_width
                y_pct = event.y / screen_height
                screenshot_click_x = int(x_pct * screenshot.size[0])
                screenshot_click_y = int(y_pct * screenshot.size[1])
                monitor_info = None
            
            # Use smart OCR processing for better accuracy
            ocr_result = self.smart_ocr.process_click_region(screenshot, screenshot_click_x, screenshot_click_y, self.debug_mode)
            
            # Add debug marker to screenshot if in debug mode
            if self.debug_mode:
                screenshot = self.screen_capture.add_debug_click_marker(
                    screenshot, x_pct=x_pct, y_pct=y_pct, marker_size=8, color="blue"
                )
            
            # Store screenshot for reuse by subsequent keyboard events
            self._last_screenshot = screenshot
            
            # Generate step description
            description = self._generate_click_description(event, ocr_result)
            
            # Use provided step number (don't increment session counter again)
            
            # Save screenshot
            screenshot_path = self.storage.save_screenshot(
                tutorial_id, 
                screenshot, 
                step_number
            )
            
            # Create step
            step = TutorialStep(
                step_id=f"step_{step_number}",
                timestamp=event.timestamp,
                step_number=step_number,
                description=description,
                screenshot_path=screenshot_path,
                event_data={
                    'x': event.x, 
                    'y': event.y, 
                    'button': event.button,
                    'is_double_click': event.is_double_click,
                    'click_count': event.click_count
                },
                ocr_text=ocr_result.cleaned_text if ocr_result.is_valid() else None,
                ocr_confidence=ocr_result.confidence if ocr_result.is_valid() else 0.0,
                coordinates=(event.x, event.y),
                coordinates_pct=(x_pct, y_pct),
                screen_dimensions=(screen_width, screen_height),
                step_type="click"
            )
            
            # Save step
            self.storage.save_tutorial_step(tutorial_id, step)
            print(f"EventProcessor: Created step {step_number}: {description}")
            
            return True
            
        except Exception as e:
            print(f"EventProcessor: Error processing mouse click: {e}")
            return False
    
    def _process_manual_capture_event(self, queued_event: QueuedEvent, tutorial_id: str, session, step_number: int) -> bool:
        """Process a queued manual capture event into a tutorial step"""
        event = queued_event.event_object
        screenshot = queued_event.screenshot
        
        if not screenshot:
            print("EventProcessor: No screenshot available for manual capture event")
            return False
        
        try:
            # Use pre-calculated coordinate info if available (same as mouse click processing)
            if queued_event.coordinate_info:
                coord_info = queued_event.coordinate_info
                screen_width = coord_info['screen_width']
                screen_height = coord_info['screen_height']
                monitor_relative_x = coord_info['monitor_relative_x']
                monitor_relative_y = coord_info['monitor_relative_y']
                monitor_info = coord_info['monitor_info']
                
                # Calculate percentage coordinates relative to the captured monitor
                if monitor_info:
                    x_pct = monitor_relative_x / monitor_info['width']
                    y_pct = monitor_relative_y / monitor_info['height']
                else:
                    x_pct = event.x / screen_width
                    y_pct = event.y / screen_height
                
                # Screenshot coordinates are the monitor-relative coordinates
                screenshot_click_x = monitor_relative_x
                screenshot_click_y = monitor_relative_y
            else:
                # Fallback to basic calculation if coordinate info not available
                print("EventProcessor: Warning - No coordinate info available for manual capture, using fallback calculation")
                screen_info = self.screen_capture.get_screen_info()
                screen_width = screen_info['width']
                screen_height = screen_info['height']
                x_pct = event.x / screen_width
                y_pct = event.y / screen_height
                screenshot_click_x = int(x_pct * screenshot.size[0])
                screenshot_click_y = int(y_pct * screenshot.size[1])
                monitor_info = None
            
            # Use smart OCR processing for better accuracy
            ocr_result = self.smart_ocr.process_click_region(screenshot, screenshot_click_x, screenshot_click_y, self.debug_mode)
            
            # Add debug marker to screenshot if in debug mode
            if self.debug_mode:
                screenshot = self.screen_capture.add_debug_click_marker(
                    screenshot, x_pct=x_pct, y_pct=y_pct, marker_size=8, color="green"
                )
            
            # Store screenshot for reuse by subsequent keyboard events
            self._last_screenshot = screenshot
            
            # Generate step description for manual capture
            description = self._generate_manual_capture_description(event, ocr_result)
            
            # Save screenshot
            screenshot_path = self.storage.save_screenshot(
                tutorial_id, 
                screenshot, 
                step_number
            )
            
            # Create step
            step = TutorialStep(
                step_id=f"step_{step_number}",
                timestamp=event.timestamp,
                step_number=step_number,
                description=description,
                screenshot_path=screenshot_path,
                event_data={'x': event.x, 'y': event.y, 'manual_capture': True},
                ocr_text=ocr_result.cleaned_text if ocr_result.is_valid() else None,
                ocr_confidence=ocr_result.confidence if ocr_result.is_valid() else 0.0,
                coordinates=(event.x, event.y),
                coordinates_pct=(x_pct, y_pct),
                screen_dimensions=(screen_width, screen_height),
                step_type="manual_capture"
            )
            
            # Save step
            self.storage.save_tutorial_step(tutorial_id, step)
            print(f"EventProcessor: Created manual capture step {step_number}: {description}")
            
            return True
            
        except Exception as e:
            print(f"EventProcessor: Error processing manual capture: {e}")
            return False
    
    def _process_keyboard_event(self, queued_event: QueuedEvent, tutorial_id: str, session, step_number: int) -> bool:
        """Process a queued keyboard event into a tutorial step"""
        event = queued_event.event_object
        
        try:
            # Skip very rapid consecutive events (debouncing)
            if (event.timestamp - session.last_event_time) < 0.05:
                return False
            session.last_event_time = event.timestamp
            
            # Handle different types of keyboard events
            if event.event_type == EventType.TEXT_INPUT:
                description = f'Type "{event.key.replace("TEXT:", "")}"'
                step_type = "type"
            elif event.is_special:
                description = f'Press {event.key}'
                step_type = "key"
            else:
                description = f'Type "{event.key}"'
                step_type = "type"
            
            # Create tutorial step for significant keyboard events
            if event.is_special or event.event_type == EventType.TEXT_INPUT:
                # Reuse last screenshot instead of capturing new one
                # This matches SCRIBE's approach and is more efficient
                screenshot = getattr(self, '_last_screenshot', None)
                
                # Fallback: capture screenshot of selected monitor or detect from mouse position
                if screenshot is None:
                    try:
                        target_monitor = 1  # Default to primary monitor
                        
                        # Check if session has a selected monitor
                        if hasattr(session, 'selected_monitor') and session.selected_monitor:
                            target_monitor = session.selected_monitor
                        else:
                            # Get current mouse position to determine which monitor to capture
                            from pynput.mouse import Controller as MouseController
                            mouse = MouseController()
                            mouse_x, mouse_y = mouse.position
                            
                            # Find which monitor contains the mouse cursor
                            screen_info = self.screen_capture.get_screen_info()
                            monitors = screen_info.get('monitors', [])
                            
                            for monitor in monitors:
                                if (monitor['left'] <= mouse_x < monitor['left'] + monitor['width'] and 
                                    monitor['top'] <= mouse_y < monitor['top'] + monitor['height']):
                                    target_monitor = monitor['id']
                                    break
                        
                        screenshot = self.screen_capture.capture_full_screen(monitor_id=target_monitor)
                    except Exception as e:
                        print(f"EventProcessor: Error detecting monitor, using primary: {e}")
                        screenshot = self.screen_capture.capture_full_screen(monitor_id=1)
                
                # Use provided step number (don't increment session counter again)
                
                # Save screenshot
                screenshot_path = None
                if screenshot:
                    screenshot_path = self.storage.save_screenshot(
                        tutorial_id, 
                        screenshot, 
                        step_number
                    )
                
                # Create step
                step = TutorialStep(
                    step_id=f"step_{step_number}",
                    timestamp=event.timestamp,
                    step_number=step_number,
                    description=description,
                    screenshot_path=screenshot_path,
                    event_data={'key': event.key, 'is_special': event.is_special},
                    step_type=step_type
                )
                
                # Save step
                self.storage.save_tutorial_step(tutorial_id, step)
                print(f"EventProcessor: Created step {step_number}: {description}")
                
                return True
            
            return False
            
        except Exception as e:
            print(f"EventProcessor: Error processing keyboard event: {e}")
            return False
    
    def _generate_click_description(self, event: MouseClickEvent, ocr_result: OCRResult) -> str:
        """Generate a human-readable description for a click event"""
        # Determine click type prefix
        if event.is_double_click or event.click_count == 2:
            click_prefix = "Double-click"
        else:
            click_prefix = "Click"
        
        # Add button specification for non-left clicks
        if event.button != "left":
            click_prefix = f"{event.button.capitalize()} {click_prefix.lower()}"
        
        if ocr_result.is_valid() and ocr_result.cleaned_text:
            text = ocr_result.cleaned_text.strip()
            
            # Handle different types of OCR results
            if ocr_result.engine == "context_analysis":
                # Context-inferred descriptions
                return f'{click_prefix} on {text}'
            elif len(text) <= 2:
                # Very short text might be a symbol or single character
                return f'{click_prefix} on "{text}" element'
            else:
                # Normal text result
                return f'{click_prefix} on "{text}"'
        else:
            # No OCR text - use coordinates with enhanced description
            return f'{click_prefix} at position ({event.x}, {event.y})'
    
    def _generate_manual_capture_description(self, event: ManualCaptureEvent, ocr_result: OCRResult) -> str:
        """Generate a human-readable description for a manual capture event"""
        if ocr_result.is_valid() and ocr_result.cleaned_text:
            text = ocr_result.cleaned_text.strip()
            
            # Handle different types of OCR results
            if ocr_result.engine == "context_analysis":
                # Context-inferred descriptions
                return f'Capture view of {text}'
            elif len(text) <= 2:
                # Very short text might be a symbol or single character
                return f'Capture view of "{text}" element'
            else:
                # Normal text result
                return f'Capture view of "{text}"'
        else:
            # No OCR text - use coordinates with enhanced description
            return f'Capture view at position ({event.x}, {event.y})'
    
    def save_raw_events(self, events: List[QueuedEvent], tutorial_id: str) -> bool:
        """Save raw events to events.json file"""
        try:
            project_path = self.storage.get_project_path(tutorial_id)
            if not project_path:
                return False
            
            # Prepare events for JSON (remove non-serializable data)
            json_events = []
            for queued_event in events:
                json_event = queued_event.event_data.copy()  # Use the pre-prepared event_data
                json_events.append(json_event)
            
            self.storage._save_events(project_path, json_events)
            print(f"EventProcessor: Saved {len(json_events)} raw events to events.json")
            return True
            
        except Exception as e:
            print(f"EventProcessor: Error saving raw events: {e}")
            return False