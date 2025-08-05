import os
import sys
import pytest
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.core.app import TutorialMakerApp

@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="GUI integration test; requires local desktop environment."
)
def test_screenshot_size_matches_screen():
    app = TutorialMakerApp(debug_mode=True)
    screen_info = app.screen_capture.get_screen_info()
    width, height = screen_info['width'], screen_info['height']
    screenshot = app.screen_capture.capture_full_screen()
    assert screenshot is not None, "Screenshot failed!"
    img_width, img_height = screenshot.size
    print(f"Screen size: {width}x{height}, Screenshot size: {img_width}x{img_height}")
    assert img_width == width and img_height == height, (
        f"Screenshot size {img_width}x{img_height} does not match screen size {width}x{height}")
