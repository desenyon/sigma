# Scripts Directory Documentation

The `scripts/` directory contains essential automation utilities for building, packaging, and distributing the Sigma application.

## Contents

### 1. `build.sh`
**Purpose**: The master build script that orchestrates the entire packaging process.
**Workflow**:
1. Checks for Python 3.
2. Cleans previous build artifacts (`dist/`, `build/`).
3. Installs build dependencies (`build`, `twine`).
4. Builds the Python package (Wheel and Source Tarball).
5. Calls `create_app.py` to generate the macOS App Bundle.
**Dependencies**: `python3`, `pip`, `build`, `twine`.

### 2. `create_app.py`
**Purpose**: Generates a native macOS `.app` bundle for Sigma.
**Details**:
- Creates the folder structure (`Sigma.app/Contents/MacOS`, `Resources`, etc.).
- Generates `Info.plist` with metadata (Bundle ID: `com.sigma.app`).
- Creates a launcher script that detects the user's Python installation (Homebrew/System) and launches the module.
- Handles icon generation (currently placeholder).
**Dependencies**: Standard Python libraries (`os`, `plistlib`, `shutil`).

## Usage

To build the entire project:

```bash
./scripts/build.sh
```

Artifacts will be placed in the `dist/` directory.
