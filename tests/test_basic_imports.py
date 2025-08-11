"""
Basic import and functionality tests that can run in CI environments
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_core_imports():
    """Test that core modules can be imported"""
    from src.core.storage import TutorialStorage, TutorialMetadata, TutorialStep
    from src.core.exporters import TutorialExporter, HTMLExporter, WordExporter, MarkdownExporter
    from src.utils.file_utils import sanitize_filename, format_duration
    
    # Test basic instantiation
    storage = TutorialStorage()
    exporter = TutorialExporter()
    
    assert storage is not None
    assert exporter is not None

def test_tutorial_metadata():
    """Test TutorialMetadata creation and serialization"""
    from src.core.storage import TutorialMetadata
    import time
    
    metadata = TutorialMetadata(
        tutorial_id="test-123",
        title="Test Tutorial",
        description="A test tutorial",
        created_at=time.time(),
        last_modified=time.time(),
        status="completed",
        step_count=5,
        duration=30.5
    )
    
    assert metadata.tutorial_id == "test-123"
    assert metadata.title == "Test Tutorial"
    assert metadata.step_count == 5
    assert metadata.duration == 30.5

def test_tutorial_step():
    """Test TutorialStep creation"""
    from src.core.storage import TutorialStep
    import time
    
    step = TutorialStep(
        step_id="step-1",
        timestamp=time.time(),
        step_number=1,
        description="Click on login button",
        screenshot_path="screenshots/step_001.png",
        coordinates=(100, 200),
        coordinates_pct=(0.1, 0.2),
        screen_dimensions=(1920, 1080),
        step_type="click",
        ocr_text="Login",
        ocr_confidence=0.95
    )
    
    assert step.step_id == "step-1"
    assert step.step_number == 1
    assert step.description == "Click on login button"
    assert step.coordinates == (100, 200)
    assert step.coordinates_pct == (0.1, 0.2)
    assert step.ocr_confidence == 0.95

def test_file_utils():
    """Test file utility functions"""
    from src.utils.file_utils import sanitize_filename, format_duration
    
    # Test filename sanitization
    assert sanitize_filename("Valid Name") == "Valid_Name"
    assert sanitize_filename("Invalid/\\:*?\"<>|Name") == "Invalid_Name"
    assert sanitize_filename("") == "untitled"
    
    # Test duration formatting
    assert format_duration(30.5) == "30.5s"
    assert format_duration(90.0) == "1m 30s"
    assert format_duration(3661.0) == "1h 1m 1s"

def test_version_info():
    """Test version information is available"""
    from src import __version__, __version_info__
    
    assert __version__ is not None
    assert __version_info__ is not None
    assert isinstance(__version_info__, tuple)
    assert len(__version_info__) >= 3

def test_exporters_instantiation():
    """Test that all exporters can be instantiated"""
    from src.core.exporters import HTMLExporter, WordExporter, MarkdownExporter, PDFExporter
    
    html_exporter = HTMLExporter()
    word_exporter = WordExporter()
    markdown_exporter = MarkdownExporter()
    pdf_exporter = PDFExporter()
    
    assert html_exporter is not None
    assert word_exporter is not None
    assert markdown_exporter is not None
    assert pdf_exporter is not None

def test_events_module_fallback():
    """Test that events module loads properly even without pynput"""
    from src.core.events import EventType, MouseClickEvent, KeyPressEvent
    
    # Test enum values
    assert EventType.MOUSE_CLICK is not None
    assert EventType.KEY_PRESS is not None
    
    # Test event creation
    mouse_event = MouseClickEvent(
        timestamp=1234567890.0,
        x=100,
        y=200,
        button="left"
    )
    
    assert mouse_event.x == 100
    assert mouse_event.y == 200
    assert mouse_event.button == "left"
    
    key_event = KeyPressEvent(
        timestamp=1234567890.0,
        key="a",
        modifiers=[]
    )
    
    assert key_event.key == "a"
    assert key_event.modifiers == []