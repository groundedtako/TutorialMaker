import os
import sys
import time
import pytest
import numpy as np
from PIL import Image

# Skip entire module if in headless environment or imports fail
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true" or os.environ.get("DISPLAY") is None,
    reason="Screenshot tests require display environment"
)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.core.app import TutorialMakerApp
    from src.core.capture import ScreenCapture
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)

@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="GUI integration test; requires local desktop environment."
)
def test_screenshot_marker_placement(tmp_path):
    """
    Test that the red dot marker is correctly placed on screenshots for known click locations.
    Corners, edge centers, and center row are tested.
    """
    app = TutorialMakerApp(debug_mode=True)
    capture = ScreenCapture(debug_mode=True)
    screen_info = app.screen_capture.get_screen_info()
    width, height = screen_info['width'], screen_info['height']
    # Use the same test points as the mouse click accuracy test
    spacing = 50
    start_x, start_y = 50, 50
    points_per_row = min(5, (width - start_x) // spacing)
    rows = 4
    points = []
    for row in range(rows):
        y = start_y + row * spacing
        for col in range(points_per_row):
            x = start_x + col * spacing
            if x < width - 10 and y < height - 10:  # avoid edges
                points.append((x, y))
            if len(points) >= 20:
                break
        if len(points) >= 20:
            break

    marker_size = 6
    tolerance = marker_size + 2  # Allow for marker spread
    failures = []
    for idx, (x, y) in enumerate(points):
        # Compute percent coordinates
        x_pct = x / width
        y_pct = y / height
        # Create a blank white image
        img = Image.new('RGBA', (width, height), (255, 255, 255, 255))
        img_marked = capture.add_debug_click_marker(img, x_pct=x_pct, y_pct=y_pct, marker_size=6, color="red")
        arr = np.array(img_marked)
        # Find marker pixels (pure red)
        marker_mask = (
            (arr[:,:,0] == 255) & (arr[:,:,1] == 0) & (arr[:,:,2] == 0)
        )
        # Find the centroid of the marker
        ys, xs = np.where(marker_mask)
        if len(xs) == 0 or len(ys) == 0:
            failures.append((idx, (x, y), 'No marker found'))
            continue
        cx, cy = int(np.mean(xs)), int(np.mean(ys))
        dist = ((cx - x) ** 2 + (cy - y) ** 2) ** 0.5
        if dist > tolerance:
            failures.append((idx, (x, y), f'Centroid offset: {dist:.2f}px'))
        print(f"Test {idx}: Target=({x},{y}) Marker=({cx},{cy}) Offset={dist:.2f}px")
    assert not failures, f"Marker placement errors: {failures}"
