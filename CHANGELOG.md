# Changelog

All notable changes to TutorialMaker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of TutorialMaker
- Cross-platform screen recording with OCR-powered step detection
- Smart region detection for accurate text capture
- Web-based tutorial editing interface
- Multiple export formats (HTML, Word, Markdown, PDF)
- Privacy-focused local-only processing
- Debug mode with visual click markers
- Session management with pause/resume functionality

### Fixed
- Stop Recording actions no longer appear in tutorials
- Coordinate transformation issues between display and OCR processing
- OCR accuracy improvements with enhanced text cleaning
- Cross-platform compatibility for Windows, macOS, and Linux

### Security
- All processing happens locally - no data sent to external services
- No admin privileges required
- Local-only OCR engines (Tesseract + EasyOCR)

## [1.0.0] - Initial Release

### Added
- Core screen recording functionality
- OCR text recognition with dual-engine support
- Tutorial generation and management
- Cross-platform executable builds
- Docker containerization
- Comprehensive CI/CD pipeline