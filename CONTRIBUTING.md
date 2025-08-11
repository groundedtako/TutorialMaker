# Contributing to TutorialMaker

Thank you for your interest in contributing to TutorialMaker! This document provides guidelines and information for contributors.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, please include as many details as possible using our bug report template.

### Suggesting Enhancements

Enhancement suggestions are welcome! Please use our feature request template and include:
- Clear description of the enhancement
- Use case or problem it solves
- Expected behavior
- Cross-platform considerations

### Code Contributions

#### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/tutorialmaker.git
   cd tutorialmaker
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]  # Install development dependencies
   ```

4. **Install System Dependencies**
   - **macOS**: `brew install tesseract`
   - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

5. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

#### Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make Changes**
   - Write clean, documented code
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation if needed

3. **Test Your Changes**
   ```bash
   # Run tests
   pytest tests/ -v --cov=src
   
   # Test cross-platform compatibility
   python main.py --debug
   python server.py --debug
   ```

4. **Commit Your Changes**
   Use conventional commits format:
   ```bash
   git commit -m "feat: add new OCR preprocessing option"
   git commit -m "fix: resolve coordinate scaling on high-DPI displays"
   git commit -m "docs: update installation instructions"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request using our PR template.

## Code Style Guidelines

### Python Code Style
- Follow PEP 8
- Use Black for code formatting: `black src/`
- Maximum line length: 100 characters
- Use type hints where possible
- Write docstrings for all public functions/classes

### Commit Message Format
We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

Examples:
```
feat(ocr): add EasyOCR fallback for better accuracy
fix(ui): resolve button positioning on small screens
docs: update cross-platform installation guide
```

## Testing Guidelines

### Test Categories
1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test component interactions
3. **Cross-Platform Tests**: Verify functionality across OS
4. **UI Tests**: Test web interface functionality

### Writing Tests
```python
import pytest
from src.core.smart_ocr import SmartOCRProcessor

def test_ocr_text_extraction():
    processor = SmartOCRProcessor()
    # Test implementation
    assert processor.process_text("sample") is not None
```

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_ocr.py -v

# Cross-platform tests
pytest tests/test_cross_platform.py -v
```

## Cross-Platform Development

### Key Considerations
1. **File Paths**: Use `pathlib.Path()` for cross-platform compatibility
2. **Dependencies**: Test on Windows, macOS, and Linux
3. **Permissions**: Handle different permission models
4. **System Integration**: Screen recording permissions vary by OS

### Testing on Multiple Platforms
- Use GitHub Actions for automated cross-platform testing
- Test locally with Docker for Linux compatibility
- Consider different Python versions (3.9+)

## Documentation

### Code Documentation
- Write clear docstrings for all public APIs
- Include parameter types and return values
- Provide usage examples for complex functions

### User Documentation
- Update README.md for user-facing changes
- Update CLAUDE.md for development guidelines
- Add screenshots for UI changes

## Performance Guidelines

### OCR Optimization
- Profile OCR operations for performance bottlenecks
- Consider caching strategies for repeated operations
- Optimize image preprocessing pipelines

### Memory Management
- Monitor memory usage during long recording sessions
- Implement cleanup for temporary files
- Consider memory-efficient image processing

## Security Considerations

### Privacy Requirements
- All processing must remain local
- No data should be sent to external services
- Temporary files should be properly cleaned up

### Permission Handling
- Request minimal necessary permissions
- Gracefully handle permission denials
- Provide clear user guidance for permission setup

## Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes (backward compatible)

### Release Checklist
1. Update CHANGELOG.md
2. Test cross-platform compatibility
3. Update documentation
4. Create release PR
5. Tag release after merge
6. Verify automated builds succeed

## Getting Help

### Communication Channels
- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and community discussion
- Pull Request Reviews: Code-specific discussion

### Documentation Resources
- README.md: User installation and usage
- CLAUDE.md: Development guidelines and architecture
- Server Usage: Web interface documentation
- Code Comments: Inline documentation

Thank you for contributing to TutorialMaker! 🚀