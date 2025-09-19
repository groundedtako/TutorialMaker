# Changelog

All notable changes to TutorialMaker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0](https://github.com/groundedtako/scribe_local/compare/v1.0.0...v1.1.0) (2025-09-19)


### Features

* add floating window toggle hotkey and fix Windows hotkey defaults ([4ec7ab4](https://github.com/groundedtako/scribe_local/commit/4ec7ab44f9b6fa0484fb84c0b80a518d3f3448b9))
* enable manual capture by default in all modes ([e537cc1](https://github.com/groundedtako/scribe_local/commit/e537cc1188d45caacfd161dde267d61d867bb302))
* extract CoordinateSystemHandler for centralized multi-monitor coordinate mapping ([690b762](https://github.com/groundedtako/scribe_local/commit/690b7623cd63d0d66f7465312848fd7ce95e0802))
* extract SessionManager for clean session lifecycle management ([e54804b](https://github.com/groundedtako/scribe_local/commit/e54804b3f313db9ce71d7ef42b79c60a9b6a2425))
* fully automated versioning and changelog generation ([1453106](https://github.com/groundedtako/scribe_local/commit/14531063cce5340b462fe4a9a0e5c61b0df9b25e))
* implement comprehensive double-click detection with system timing ([4def3a5](https://github.com/groundedtako/scribe_local/commit/4def3a542998fee5a35eef0f721f6338cb8cd558))
* implement comprehensive multi-monitor recording support with screen selection ([73e42fb](https://github.com/groundedtako/scribe_local/commit/73e42fb01516d0f873ee3c51d30bfd9c63f74927))
* implement Delete All Tutorials and optimize Export All with concurrency ([b30d4e6](https://github.com/groundedtako/scribe_local/commit/b30d4e6ed835439a899bf33d5eed31f7cea8e764))
* implement manual screenshot capture with keyboard hotkey ([6a58d2a](https://github.com/groundedtako/scribe_local/commit/6a58d2a57df5c102c0fafac9c468ac1704580255))
* implement persistent monitor selection and smart control placement ([7099686](https://github.com/groundedtako/scribe_local/commit/7099686b596bc7b84f0a7182c9b5e12be634676b))
* implement tutorial export and formatting improvements with preview fix ([c888d28](https://github.com/groundedtako/scribe_local/commit/c888d28cbc26cf0b9da4e1ba9ea07c381a394a69))
* simplify automated release system with release-please ([b8706cb](https://github.com/groundedtako/scribe_local/commit/b8706cb3a12e77ff5b46df3c2af0e814221ae6e1))


### Bug Fixes

* correct release-please workflow configuration ([0f47275](https://github.com/groundedtako/scribe_local/commit/0f472753ca15d52fb0914cc431883dc00dcb94df))
* handle multiple screens + keyboard filtering ([04a916f](https://github.com/groundedtako/scribe_local/commit/04a916f07cc976c73ccfd0ab5c1b702fc384ecd4))
* implement real-time step feedback during recording ([985d326](https://github.com/groundedtako/scribe_local/commit/985d326b0af18e39e8427cdfb9f2784a8f6b08b4))
* improve desktop GUI floating control panel UX and fix compatibility issues ([85c86e4](https://github.com/groundedtako/scribe_local/commit/85c86e472c607408a6110ddd990bf4dc1c36a585))
* improve multi-monitor coordinate mapping and web UI click indicators ([396ec20](https://github.com/groundedtako/scribe_local/commit/396ec206845dafadde0bf532440ad6096a4c6f40))
* resolve CI/CD test failures for headless environments ([97925c4](https://github.com/groundedtako/scribe_local/commit/97925c47df739d2639fcabb33bfc5d4cbc73e61c))
* resolve desktop app tutorial list layout issues on Windows ([0e585dc](https://github.com/groundedtako/scribe_local/commit/0e585dc12c810897376293f520c7dab4a0a32709))
* resolve GitHub Actions pipeline and executable build issues ([f506665](https://github.com/groundedtako/scribe_local/commit/f506665f23d401d6873b34ec1aabaea15433ef31))

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
