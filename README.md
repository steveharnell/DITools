# DITools

**Professional Digital Imaging Toolkit for Film & Television Production**

DITools is a comprehensive digital imaging solution engineered to optimize on-set workflows and expedite the wrap process across commercial, television, and film productions.

## Looking for the Latest Release?

The latest release is always available [here](#), and you can also browse [previous releases](#).

## Key Features

### Automated Project Organization
Generate structured project directories with customizable transcode and DIT folder hierarchies to ensure consistent file management across productions.

### Reliable Directory Synchronization
Transfer files between storage locations with real-time progress tracking, cancellation capabilities, and detailed logging. Supports simultaneous multi-destination syncing with independent source/destination pairs.

### Smart Rsync Detection
DITools automatically detects and prioritizes Homebrew-installed rsync over the outdated macOS system binary. The detected rsync version and path are displayed in the Sync status log on launch. If Homebrew rsync is not found, a warning is shown with installation guidance.

### xxHash64 Checksum Support
When Homebrew rsync 3.2.0+ is detected, an optional xxHash64 checksum mode is available in the Sync module. xxHash64 provides significantly faster checksum verification compared to the default MD5, which is especially useful for large camera original transfers. Requires [Homebrew](https://brew.sh/) rsync 3.2.0 or newer.

### Cross-Drive File Verification
Ensure data integrity with comprehensive file comparison across client drives, complete with verification reports.

### Advanced Render Verification
Validate transcoded files against camera originals using functionality inspired by John Spellman's industry-standard RenderCheck AppleScript.

### Directory Tree Generation
Export comprehensive text-based maps of file systems with customizable filtering options and human-readable size calculations for efficient documentation and auditing. *(Credit: Michael Romano)*

### Workflow Optimization Tools
Streamline post-production with utilities such as automatic .drx file cleanup after DaVinci Resolve still extraction.

## Technical Specifications

- Developed entirely in Python 3 with zero external dependencies
- Compiled via PyInstaller for maximum macOS compatibility and portability
- macOS only
- Automatically detects and uses Homebrew rsync (`/opt/homebrew/bin/rsync`) when available, falling back to the system rsync if necessary
- xxHash64 checksum support requires rsync 3.2.0+, installable via [Homebrew](https://brew.sh/)

> **Note:** This beta release is provided as-is with no warranty. Test thoroughly in non-critical environments before deployment in production scenarios.

##

[![Watch the video](https://vumbnail.com/1063427223.jpg)](https://vimeo.com/1063427223)
