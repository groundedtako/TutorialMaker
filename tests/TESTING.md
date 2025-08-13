# Testing Strategy for TutorialMaker

## Overview

This document outlines our comprehensive testing strategy to ensure smooth refactoring and reliable functionality.

## Testing Philosophy

**Test-Driven Refactoring**: Before making changes, write tests that validate current behavior, then refactor while keeping tests green.

## Test Structure

```
tests/
├── __init__.py
├── test_event_processor.py      # Unit tests for EventProcessor
├── test_integration_simple.py   # Simple integration tests
├── test_coordinate_fix.py       # Coordinate system validation
└── test_integration.py         # Full integration tests (WIP)
```

## Test Categories

### 1. Unit Tests
**Purpose**: Test individual components in isolation
**Location**: `tests/test_event_processor.py`

**Coverage**:
- ✅ EventProcessor mouse click processing with coordinate info
- ✅ EventProcessor mouse click processing without coordinate info (fallback)
- ✅ EventProcessor keyboard event processing
- ✅ Multi-event processing integration
- ✅ Raw event JSON serialization

**Key Test Cases**:
```python
def test_process_mouse_click_with_coordinate_info():
    """Validates that pre-calculated coordinates are used correctly"""
    
def test_coordinate_calculation_accuracy():
    """Ensures coordinate transformations are mathematically correct"""
```

### 2. Integration Tests
**Purpose**: Test component interactions
**Location**: `tests/test_integration_simple.py`

**Coverage**:
- ✅ EventQueue ↔ EventProcessor integration
- ✅ Coordinate system preservation through pipeline
- ✅ Event state transitions (RECORDING → STOPPED → PROCESSING → IDLE)

### 3. Coordinate System Validation
**Purpose**: Ensure multi-monitor coordinate mapping accuracy
**Location**: `tests/test_coordinate_fix.py`

**Coverage**:
- ✅ Coordinate info storage and retrieval
- ✅ Percentage calculation accuracy
- ✅ Monitor-relative coordinate transformations

## Running Tests

### Test Suite Management
**Primary Method**: Use the comprehensive test suite manager
```bash
# Run all tests with clean output
python run_tests.py

# Run with detailed debug output
python run_tests.py --debug

# Keep test artifacts for debugging
python run_tests.py --keep-artifacts

# List all discovered tests
python run_tests.py --list

# Get help
python run_tests.py --help
```

### Simple Test Runner
**Quick Method**: Use the simple test runner for basic validation
```bash
# Run all core tests quickly
python test_runner.py
```

### Individual Test Files
**Development Method**: Run individual tests during development
```bash
# Run EventProcessor unit tests
python tests/test_event_processor.py

# Run integration tests
python tests/test_integration_simple.py

# Run coordinate validation
python test_coordinate_fix.py
```

## Test Strategy for Refactoring

### Before Refactoring
1. **Write Characterization Tests**: Capture current behavior
2. **Validate Edge Cases**: Test multi-monitor scenarios
3. **Document Expected Behavior**: Clear test descriptions

### During Refactoring
1. **Keep Tests Green**: Tests should pass throughout refactoring
2. **Refactor Tests Too**: Update tests to match new architecture
3. **Add New Tests**: Cover new functionality

### After Refactoring
1. **Add Integration Tests**: Ensure components work together
2. **Performance Tests**: Validate no performance regression
3. **User Acceptance Tests**: Manual validation of key workflows

## Key Test Patterns

### 1. Mock Setup Pattern
```python
def setup_method(self):
    """Set up test fixtures with mocks"""
    self.mock_screen_capture = Mock()
    self.mock_storage = Mock()
    # ... set up all dependencies
```

### 2. Coordinate Validation Pattern
```python
def test_coordinate_accuracy(self):
    """Test coordinate transformations"""
    # Given: Global coordinates and monitor info
    # When: Transform to monitor-relative
    # Then: Verify mathematical accuracy
    assert abs(actual - expected) < 0.001
```

### 3. State Transition Pattern
```python
def test_event_queue_states(self):
    """Test state machine transitions"""
    queue.start_recording()
    assert queue.state == QueueState.RECORDING
    
    queue.stop_recording()
    assert queue.state == QueueState.STOPPED
```

## Future Testing Needs

### Immediate (Next Refactoring Steps)
- [ ] **SessionManager Tests**: When extracting session logic
- [ ] **CoordinateHandler Tests**: When centralizing coordinate logic
- [ ] **E2E Screenshot Tests**: Validate screenshot capture accuracy

### Medium Term
- [ ] **Performance Tests**: Measure event processing throughput
- [ ] **Memory Tests**: Ensure no memory leaks in long sessions
- [ ] **Cross-Platform Tests**: Windows/Mac compatibility

### Long Term
- [ ] **Visual Regression Tests**: OCR accuracy validation
- [ ] **User Journey Tests**: Complete recording workflows
- [ ] **Stress Tests**: Large tutorials, many events

## Testing Tools

### Current
- **unittest.mock**: For dependency mocking
- **pytest** (when available): Test runner and fixtures
- **Manual assertions**: Simple validation

### Future Considerations
- **pytest-cov**: Code coverage measurement
- **pytest-benchmark**: Performance testing
- **hypothesis**: Property-based testing for coordinate edge cases

## Continuous Testing

### Pre-Commit Testing
```bash
# Quick validation before committing
python test_runner.py

# Comprehensive testing before major commits
python run_tests.py

# Debug mode if issues found
python run_tests.py --debug
```

### Refactoring Checklist
- [ ] All existing tests pass
- [ ] New functionality has tests
- [ ] Edge cases are covered
- [ ] Integration points are tested
- [ ] Documentation is updated

## Test Data Management

### Mock Data Patterns
```python
# Standard test event
test_event = MouseClickEvent(
    x=500, y=300, button='left', 
    pressed=True, timestamp=time.time()
)

# Standard coordinate info
coordinate_info = {
    'screen_width': 1920,
    'screen_height': 1080,
    'monitor_relative_x': 200,
    'monitor_relative_y': 150,
    'monitor_info': {
        'id': 1, 'width': 800, 'height': 600,
        'left': 300, 'top': 150
    }
}
```

## Debugging Failed Tests

### Common Issues
1. **Mock State Pollution**: Reset mocks between tests
2. **Coordinate Calculation Errors**: Validate math with known values
3. **Event Object Inconsistencies**: Check event parameter names

### Debug Techniques
```python
# Add debug output to tests
print(f"Actual: {actual}, Expected: {expected}")

# Inspect mock calls
print(f"Mock calls: {mock.call_args_list}")

# Validate intermediate values
assert intermediate_result == expected_intermediate
```

## Success Metrics

### Code Quality
- **Test Coverage**: Aim for >80% on core components
- **Test Speed**: Unit tests <1s, integration tests <5s
- **Test Reliability**: No flaky tests

### Refactoring Safety
- **Zero Regressions**: All existing functionality preserved
- **Clear Interfaces**: Well-tested component boundaries
- **Maintainable Tests**: Easy to understand and modify

---

**Remember**: Tests are not just for catching bugs—they're documentation of how the system should behave and enable confident refactoring.