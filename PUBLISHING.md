
# 📦 Alternative Publishing Methods for Sigma

While PyPI (PIP) is the standard distribution channel for Python packages, Sigma's nature as a complex, terminal-based application with specific system dependencies makes alternative distribution methods highly relevant.

## 1. 🐳 Docker Container Registry

Publishing Sigma as a Docker image ensures a completely consistent environment for all users, eliminating issues with Python versions, system dependencies (like TA-Lib), and OS differences.

### Workflow
1.  **Build**: Create a `Dockerfile` that installs Python, dependencies, and the Sigma application.
2.  **Tag**: Version the image (e.g., `sigma:3.6.1`).
3.  **Push**: Upload to Docker Hub or GitHub Container Registry (GHCR).

### Pros & Cons
*   **Pros**:
    *   **Zero Dependency Hell**: Works exactly as tested.
    *   **Isolation**: Doesn't clutter the user's system Python.
    *   **Security**: Can be scanned for vulnerabilities.
*   **Cons**:
    *   **Overhead**: Requires Docker engine installed.
    *   **Integration**: Harder to interact with local files (requires volume mounting).

### Configuration
**Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install .
ENTRYPOINT ["sigma"]
```

**Command**:
```bash
docker build -t sigma/terminal:latest .
docker push sigma/terminal:latest
```

---

## 2. 🍺 Homebrew Tap (macOS/Linux)

Homebrew is the de facto package manager for macOS and is popular on Linux. Creating a custom "Tap" allows users to install Sigma with `brew install sigma`.

### Workflow
1.  **Create Formula**: Write a Ruby script (`sigma.rb`) defining the download URL (e.g., GitHub Release tarball) and dependencies.
2.  **Host Tap**: Create a GitHub repo named `homebrew-sigma`.
3.  **Install**: Users run `brew tap sigma/sigma` then `brew install sigma`.

### Pros & Cons
*   **Pros**:
    *   **Native Feel**: Installs to system path, updates managed by `brew upgrade`.
    *   **Dependency Management**: Automatically handles Python installation.
    *   **Trust**: Users trust Homebrew formulas.
*   **Cons**:
    *   **Maintenance**: Needs updates for every release.
    *   **Platform Limited**: Primarily macOS/Linux.

### Configuration
**sigma.rb**:
```ruby
class Sigma < Formula
  desc "Elite Financial Research Terminal"
  homepage "https://github.com/sigma/terminal"
  url "https://github.com/sigma/terminal/archive/v3.6.1.tar.gz"
  sha256 "<checksum>"
  license "Proprietary"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end
end
```

---

## 3. 📦 Standalone Binary (PyInstaller)

Compile Sigma into a single executable file that requires no Python installation on the user's machine.

### Workflow
1.  **Freeze**: Use `PyInstaller` or `Nuitka` to bundle the app and interpreter.
2.  **Distribute**: Upload the binary to GitHub Releases or a website.
3.  **Run**: User downloads and runs `./sigma`.

### Pros & Cons
*   **Pros**:
    *   **Portability**: Runs anywhere (matching the OS it was built on).
    *   **Simplicity**: No installation process.
*   **Cons**:
    *   **File Size**: Large binaries (embeds Python).
    *   **Startup Time**: Slower initial launch (unpacking).
    *   **Updates**: No built-in update mechanism.

### Configuration
**Command**:
```bash
pyinstaller --name sigma --onefile --add-data "sigma/ui:sigma/ui" sigma/__main__.py
```
