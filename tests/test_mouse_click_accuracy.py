import time
import os
import pytest
from pynput.mouse import Controller, Button
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Import the app and storage classes
from src.core.app import TutorialMakerApp

@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="GUI integration test; requires local desktop environment."
)
def test_mouse_click_accuracy(tmp_path):
    """
    Integration test: Simulate multiple mouse clicks and report the accuracy for each.
    """
    app = TutorialMakerApp(debug_mode=True)
    tutorial_id = app.new_tutorial("Accuracy Test")
    app.start_recording()

    mouse = Controller()
    # Generate 20 test points, 50x50 apart, starting from (50, 50)
    screen_info = app.screen_capture.get_screen_info()
    width, height = screen_info['width'], screen_info['height']
    test_points = []
    spacing = 50
    start_x, start_y = 50, 50
    points_per_row = min(5, (width - start_x) // spacing)
    rows = 4
    for row in range(rows):
        y = start_y + row * spacing
        for col in range(points_per_row):
            x = start_x + col * spacing
            if x < width - 10 and y < height - 10:  # avoid edges
                test_points.append((x, y))
            if len(test_points) >= 20:
                break
        if len(test_points) >= 20:
            break
    results = []

    for idx, (test_x, test_y) in enumerate(test_points):
        mouse.position = (test_x, test_y)
        time.sleep(0.3)  # Allow time for mouse to move
        mouse.press(Button.left)
        mouse.release(Button.left)
        time.sleep(0.5)  # Allow time for event processing

    app.stop_recording()
    steps = app.storage.load_tutorial_steps(tutorial_id)
    click_steps = [s for s in steps if getattr(s, 'step_type', None) == "click"]
    assert len(click_steps) >= len(test_points), f"Expected at least {len(test_points)} click steps, got {len(click_steps)}"

    print("\nMouse Click Accuracy Report:")
    print("Idx | Target (x, y)      | Recorded (x, y)    | dx    | dy    | Euclidean Error")
    print("----+--------------------+--------------------+-------+-------+-----------------")
    for idx, ((target_x, target_y), step) in enumerate(zip(test_points, click_steps[-len(test_points):])):
        recorded_x, recorded_y = step.coordinates
        if hasattr(step, 'coordinates_pct'):
            rx_pct, ry_pct = step.coordinates_pct
            print(f"   Percent: ({rx_pct:.4f}, {ry_pct:.4f})")
        dx = recorded_x - target_x
        dy = recorded_y - target_y
        error = (dx ** 2 + dy ** 2) ** 0.5
        results.append(error)
        print(f"{idx:>3} | ({target_x:>4}, {target_y:>4}) | ({recorded_x:>4}, {recorded_y:>4}) | {dx:>5} | {dy:>5} | {error:>15.2f}")

    avg_error = sum(results) / len(results)
    max_error = max(results)
    print(f"\nSummary: Avg Error = {avg_error:.2f} px, Max Error = {max_error:.2f} px\n")
    # Optional: assert max error within reasonable threshold
    assert max_error < 20, f"Max error too high: {max_error}px"
