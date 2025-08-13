"""
Simple test runner - alternative to run_tests.py for basic usage
"""

import sys
import time
from pathlib import Path

def run_all_tests():
    """Run all tests with simple output"""
    print("Running TutorialMaker Test Suite")
    print("=" * 40)
    
    tests_run = 0
    tests_passed = 0
    start_time = time.time()
    
    # Add project root and src to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))
    
    # Test 1: Coordinate Fix
    print("1. Coordinate System Tests...", end=" ")
    try:
        import test_coordinate_fix
        test_coordinate_fix.test_coordinate_info_storage()
        print("PASS")
        tests_passed += 1
    except Exception as e:
        print(f"FAIL - {e}")
    tests_run += 1
    
    # Test 2: Event Processor
    print("2. Event Processor Tests...", end=" ")
    try:
        from test_event_processor import TestEventProcessor
        test_instance = TestEventProcessor()
        test_instance.setup_method()
        
        test_instance.test_process_mouse_click_with_coordinate_info()
        test_instance.test_process_mouse_click_without_coordinate_info()
        test_instance.test_process_keyboard_event_special_key()
        test_instance.test_process_events_to_steps_integration()
        test_instance.test_save_raw_events()
        
        print("PASS")
        tests_passed += 1
    except Exception as e:
        print(f"FAIL - {e}")
    tests_run += 1
    
    # Test 3: Integration Tests
    print("3. Integration Tests...", end=" ")
    try:
        from test_integration_simple import run_simple_integration_tests
        run_simple_integration_tests()
        print("PASS")
        tests_passed += 1
    except Exception as e:
        print(f"FAIL - {e}")
    tests_run += 1
    
    # Test 4: Session Manager Tests
    print("4. Session Manager Tests...", end=" ")
    try:
        from test_session_manager import run_session_manager_tests
        run_session_manager_tests()
        print("PASS")
        tests_passed += 1
    except Exception as e:
        print(f"FAIL - {e}")
    tests_run += 1
    
    # Summary
    duration = time.time() - start_time
    print("=" * 40)
    print(f"Tests run: {tests_run}")
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_run - tests_passed}")
    print(f"Duration: {duration:.2f}s")
    
    if tests_passed == tests_run:
        print("\nALL TESTS PASSED!")
        return True
    else:
        print(f"\n{tests_run - tests_passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)