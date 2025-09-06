## Coding Conventions

This section outlines the coding conventions and style guidelines that the project assistant adheres to when reading or modifying code.

### Core Principles:
- **Adherence to Existing Conventions**: Rigorously adheres to existing project conventions. Analyzes surrounding code, tests, and configuration first.
- **Library/Framework Usage**: Never assumes a library/framework is available or appropriate. Verifies its established usage within the project (checks imports, configuration files like 'package.json', 'Cargo.toml', 'requirements.txt', 'build.gradle', etc., or observes neighboring files) before employing it.
- **Style & Structure**: Mimics the style (formatting, naming), structure, framework choices, typing, and architectural patterns of existing code in the project.
- **Idiomatic Changes**: Understands the local context (imports, functions/classes) to ensure changes integrate naturally and idiomatically.
- **Comments**: Adds code comments sparingly. Focuses on *why* something is done, especially for complex logic, rather than *what* is done. Only adds high-value comments if necessary for clarity or if requested by the user. Never talks to the user or describes changes through comments.
