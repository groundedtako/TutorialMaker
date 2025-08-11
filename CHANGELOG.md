# Changelog

All notable changes to TutorialMaker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0](https://github.com/groundedtako/scribe_local/compare/v1.0.0...v1.1.0) (2025-08-11)


### Features

* fully automated versioning and changelog generation ([1453106](https://github.com/groundedtako/scribe_local/commit/14531063cce5340b462fe4a9a0e5c61b0df9b25e))
* simplify automated release system with release-please ([b8706cb](https://github.com/groundedtako/scribe_local/commit/b8706cb3a12e77ff5b46df3c2af0e814221ae6e1))


### Bug Fixes

* resolve CI/CD test failures for headless environments ([97925c4](https://github.com/groundedtako/scribe_local/commit/97925c47df739d2639fcabb33bfc5d4cbc73e61c))

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
