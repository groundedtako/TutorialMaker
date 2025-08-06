"""
Route helper functions to break up large route handlers
"""

from flask import render_template
from typing import Optional, List, Tuple, Any
import traceback

from ..core.storage import TutorialMetadata, TutorialStep
from ..utils.api_utils import APIException


def load_and_validate_tutorial(storage, tutorial_id: str) -> Tuple[Optional[TutorialMetadata], List[TutorialStep]]:
    """
    Load tutorial metadata and steps, with validation
    
    Args:
        storage: TutorialStorage instance
        tutorial_id: Tutorial ID to load
        
    Returns:
        Tuple of (metadata, validated_steps)
        
    Raises:
        APIException: If tutorial not found or invalid
    """
    metadata = storage.load_tutorial_metadata(tutorial_id)
    if not metadata:
        raise APIException(f"Tutorial {tutorial_id} not found", status_code=404)
    
    steps = storage.load_tutorial_steps(tutorial_id)
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
            print(f"Error validating step {i}: {e}")
            # Skip invalid steps but continue processing
            continue
    
    return metadata, validated_steps


def render_tutorial_page(metadata: TutorialMetadata, steps: List[TutorialStep], tutorial_id: str, dev_mode: bool = False) -> str:
    """
    Render the tutorial page template
    
    Args:
        metadata: Tutorial metadata
        steps: List of tutorial steps
        tutorial_id: Tutorial ID
        dev_mode: Whether in development mode
        
    Returns:
        Rendered HTML string
    """
    # Convert steps to display format
    display_steps = []
    for step in steps:
        # Handle potential missing attributes gracefully
        step_data = {
            'step_id': getattr(step, 'step_id', f'step_{len(display_steps)}'),
            'step_number': getattr(step, 'step_number', len(display_steps) + 1),
            'description': getattr(step, 'description', 'No description'),
            'screenshot_path': getattr(step, 'screenshot_path', ''),
            'coordinates': getattr(step, 'coordinates', None),
            'coordinates_pct': getattr(step, 'coordinates_pct', None),
            'ocr_text': getattr(step, 'ocr_text', ''),
            'ocr_confidence': getattr(step, 'ocr_confidence', 0),
            'timestamp': getattr(step, 'timestamp', 0)
        }
        display_steps.append(type('Step', (), step_data))
    
    return render_template(
        'tutorial.html',
        metadata=metadata,
        steps=display_steps,
        tutorial_id=tutorial_id,
        dev_mode=dev_mode
    )


def handle_tutorial_error(tutorial_id: str, error: Exception) -> Tuple[str, int]:
    """
    Handle errors during tutorial loading/processing
    
    Args:
        tutorial_id: Tutorial ID that caused the error
        error: Exception that occurred
        
    Returns:
        Tuple of (error page HTML, status code)
    """
    print(f"Error loading tutorial {tutorial_id}: {error}")
    print(traceback.format_exc())
    
    if isinstance(error, APIException):
        return render_template(
            'tutorial_not_found.html', 
            tutorial_id=tutorial_id,
            error_message=error.message
        ), error.status_code
    
    # Generic server error
    return render_template(
        'error.html',
        error_message="An error occurred while loading the tutorial",
        details=str(error)
    ), 500


def update_tutorial_metadata(storage, tutorial_id: str, metadata_updates: dict) -> bool:
    """
    Update tutorial metadata
    
    Args:
        storage: TutorialStorage instance
        tutorial_id: Tutorial ID to update
        metadata_updates: Dictionary of metadata updates
        
    Returns:
        True if successful
        
    Raises:
        APIException: If update fails
    """
    try:
        # Load existing metadata
        metadata = storage.load_tutorial_metadata(tutorial_id)
        if not metadata:
            raise APIException("Tutorial not found", status_code=404)
        
        # Update fields if provided
        if 'title' in metadata_updates:
            metadata.title = metadata_updates['title']
        if 'description' in metadata_updates:
            metadata.description = metadata_updates['description']
        
        # Save updated metadata
        success = storage.save_tutorial_metadata(tutorial_id, metadata)
        if not success:
            raise APIException("Failed to save metadata", status_code=500)
        
        return True
        
    except Exception as e:
        if isinstance(e, APIException):
            raise
        raise APIException(f"Failed to update metadata: {str(e)}", status_code=500)


def update_tutorial_steps(storage, tutorial_id: str, steps_updates: List[dict]) -> bool:
    """
    Update tutorial steps
    
    Args:
        storage: TutorialStorage instance
        tutorial_id: Tutorial ID to update
        steps_updates: List of step updates
        
    Returns:
        True if successful
        
    Raises:
        APIException: If update fails
    """
    try:
        from ..core.storage import TutorialStep
        
        # Convert step updates to TutorialStep objects
        updated_steps = []
        for step_data in steps_updates:
            step = TutorialStep(
                step_id=step_data.get('step_id'),
                step_number=step_data.get('step_number', len(updated_steps) + 1),
                description=step_data.get('description', ''),
                screenshot_path=step_data.get('screenshot_path', ''),
                coordinates=step_data.get('coordinates'),
                coordinates_pct=step_data.get('coordinates_pct'),
                ocr_text=step_data.get('ocr_text', ''),
                ocr_confidence=step_data.get('ocr_confidence', 0),
                timestamp=step_data.get('timestamp', 0)
            )
            updated_steps.append(step)
        
        # Save updated steps
        success = storage.save_tutorial_steps(tutorial_id, updated_steps)
        if not success:
            raise APIException("Failed to save steps", status_code=500)
        
        # Update step count in metadata
        metadata = storage.load_tutorial_metadata(tutorial_id)
        if metadata:
            metadata.step_count = len(updated_steps)
            storage.save_tutorial_metadata(tutorial_id, metadata)
        
        return True
        
    except Exception as e:
        if isinstance(e, APIException):
            raise
        raise APIException(f"Failed to update steps: {str(e)}", status_code=500)


def delete_tutorial_step(storage, tutorial_id: str, step_id: str) -> bool:
    """
    Delete a specific tutorial step
    
    Args:
        storage: TutorialStorage instance
        tutorial_id: Tutorial ID
        step_id: Step ID to delete
        
    Returns:
        True if successful
        
    Raises:
        APIException: If deletion fails
    """
    try:
        # Load existing steps
        steps = storage.load_tutorial_steps(tutorial_id)
        if not steps:
            raise APIException("Tutorial steps not found", status_code=404)
        
        # Find and remove the step
        original_count = len(steps)
        updated_steps = [step for step in steps if getattr(step, 'step_id', None) != step_id]
        
        if len(updated_steps) == original_count:
            raise APIException("Step not found", status_code=404)
        
        # Renumber remaining steps
        for i, step in enumerate(updated_steps):
            step.step_number = i + 1
        
        # Save updated steps
        success = storage.save_tutorial_steps(tutorial_id, updated_steps)
        if not success:
            raise APIException("Failed to save updated steps", status_code=500)
        
        # Update step count in metadata
        metadata = storage.load_tutorial_metadata(tutorial_id)
        if metadata:
            metadata.step_count = len(updated_steps)
            storage.save_tutorial_metadata(tutorial_id, metadata)
        
        return True
        
    except Exception as e:
        if isinstance(e, APIException):
            raise
        raise APIException(f"Failed to delete step: {str(e)}", status_code=500)


def format_export_results(results: dict) -> dict:
    """
    Format export results for consistent API response
    
    Args:
        results: Raw export results from exporters
        
    Returns:
        Formatted results dictionary
    """
    formatted_results = {}
    
    for format_name, result in results.items():
        if isinstance(result, str):
            if result.startswith("Error:"):
                formatted_results[format_name] = {
                    "success": False,
                    "error": result,
                    "path": None
                }
            else:
                # Extract filename from path
                import os
                filename = os.path.basename(result)
                formatted_results[format_name] = {
                    "success": True,
                    "path": result,
                    "filename": filename
                }
        else:
            # Handle unexpected result format
            formatted_results[format_name] = {
                "success": False,
                "error": "Unexpected result format",
                "path": None
            }
    
    return formatted_results