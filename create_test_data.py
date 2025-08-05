#!/usr/bin/env python3
"""
Create test tutorial data for web server testing
"""

import time
from src.core.app import TutorialMakerApp
from src.core.storage import TutorialStep
from PIL import Image, ImageDraw

def create_test_screenshot(width=800, height=600, text="Sample Screenshot"):
    """Create a test screenshot image"""
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw some UI elements
    draw.rectangle([50, 50, width-50, 100], fill='lightblue', outline='blue')
    draw.text((60, 65), text, fill='black')
    
    # Draw some buttons
    draw.rectangle([100, 150, 200, 180], fill='lightgreen', outline='green')
    draw.text((125, 160), "Button 1", fill='black')
    
    draw.rectangle([100, 200, 200, 230], fill='lightcoral', outline='red')
    draw.text((125, 210), "Button 2", fill='black')
    
    return img

def main():
    print("Creating test tutorial data...")
    
    # Initialize app
    app = TutorialMakerApp(debug_mode=True)
    
    # Create first test tutorial
    tutorial_id_1 = app.new_tutorial("Sample Login Tutorial", "A tutorial showing how to log into the system")
    
    # Create some test steps
    test_screenshot = create_test_screenshot(800, 600, "Login Page")
    
    # Step 1: Click username field
    step1 = TutorialStep(
        step_id="step_1",
        timestamp=time.time(),
        step_number=1,
        description='Click on "Username" field',
        screenshot_path=None,  # We'll save this manually
        event_data={'x': 300, 'y': 200, 'button': 'left'},
        ocr_text="Username",
        ocr_confidence=0.95,
        coordinates=(300, 200),
        coordinates_pct=(0.375, 0.333),  # 300/800, 200/600
        screen_dimensions=(800, 600),
        step_type="click"
    )
    
    # Save screenshot for step 1
    screenshot_path_1 = app.storage.save_screenshot(tutorial_id_1, test_screenshot, 1)
    step1.screenshot_path = screenshot_path_1
    app.storage.save_tutorial_step(tutorial_id_1, step1)
    
    # Step 2: Type username
    step2 = TutorialStep(
        step_id="step_2",
        timestamp=time.time() + 1,
        step_number=2,
        description='Type "john.doe" in username field',
        screenshot_path=None,
        event_data={'text': 'john.doe'},
        step_type="type"
    )
    
    test_screenshot_2 = create_test_screenshot(800, 600, "Username Entered")
    screenshot_path_2 = app.storage.save_screenshot(tutorial_id_1, test_screenshot_2, 2)
    step2.screenshot_path = screenshot_path_2
    app.storage.save_tutorial_step(tutorial_id_1, step2)
    
    # Step 3: Click password field
    step3 = TutorialStep(
        step_id="step_3",
        timestamp=time.time() + 2,
        step_number=3,
        description='Click on "Password" field',
        screenshot_path=None,
        event_data={'x': 300, 'y': 250, 'button': 'left'},
        ocr_text="Password",
        ocr_confidence=0.92,
        coordinates=(300, 250),
        coordinates_pct=(0.375, 0.417),  # 300/800, 250/600
        screen_dimensions=(800, 600),
        step_type="click"
    )
    
    test_screenshot_3 = create_test_screenshot(800, 600, "Password Field")
    screenshot_path_3 = app.storage.save_screenshot(tutorial_id_1, test_screenshot_3, 3)
    step3.screenshot_path = screenshot_path_3
    app.storage.save_tutorial_step(tutorial_id_1, step3)
    
    # Complete the tutorial
    app.storage.update_tutorial_status(tutorial_id_1, "completed")
    
    # Create second test tutorial
    tutorial_id_2 = app.new_tutorial("Quick Navigation Guide", "How to navigate the main dashboard")
    
    # Add one step to second tutorial
    step_nav = TutorialStep(
        step_id="step_1",
        timestamp=time.time(),
        step_number=1,
        description='Click on "Dashboard" menu item',
        screenshot_path=None,
        event_data={'x': 150, 'y': 100, 'button': 'left'},
        ocr_text="Dashboard",
        ocr_confidence=0.98,
        coordinates=(150, 100),
        coordinates_pct=(0.1875, 0.167),  # 150/800, 100/600
        screen_dimensions=(800, 600),
        step_type="click"
    )
    
    test_screenshot_nav = create_test_screenshot(800, 600, "Navigation Menu")
    screenshot_path_nav = app.storage.save_screenshot(tutorial_id_2, test_screenshot_nav, 1)
    step_nav.screenshot_path = screenshot_path_nav
    app.storage.save_tutorial_step(tutorial_id_2, step_nav)
    
    app.storage.update_tutorial_status(tutorial_id_2, "completed")
    
    print(f"✅ Created test tutorial 1: {tutorial_id_1}")
    print(f"✅ Created test tutorial 2: {tutorial_id_2}")
    print(f"📁 Data saved to: {app.storage.base_path}")
    print("\nNow you can test the web server:")
    print("1. Run: python3 main.py")
    print("2. Type: web")
    print("3. Or directly: python3 start_web_server.py")

if __name__ == "__main__":
    main()