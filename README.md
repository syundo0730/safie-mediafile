# Safie Media File Downloader

[![Lint and Test](https://github.com/example/safie-mediafile/actions/workflows/lint-and-test.yml/badge.svg)](https://github.com/example/safie-mediafile/actions/workflows/lint-and-test.yml)
[![PyPI version](https://img.shields.io/pypi/v/safie-mediafile.svg)](https://pypi.org/project/safie-mediafile/)
[![Python Versions](https://img.shields.io/pypi/pyversions/safie-mediafile.svg)](https://pypi.org/project/safie-mediafile/)
[![License](https://img.shields.io/pypi/l/safie-mediafile.svg)](https://github.com/example/safie-mediafile/blob/main/LICENSE)

A Python library and command-line tool for downloading media files from Safie cameras.

## Installation

### Library Only

If you want to use only the library functionality:

```bash
# Install from the current directory
pip install .

# Or install from PyPI (not published yet)
pip install safie-mediafile
```

### Library with CLI Tool

If you also want to use the command-line tool:

```bash
# Install from the current directory
pip install ".[cli]"

# Or install from PyPI (not published yet)
pip install "safie-mediafile[cli]"
```

## Usage

### Command Line Interface

You can download media files using either the device serial number or device name:

```bash
# Using serial number
safie-mediafile --serial 201055433 2024-03-22T10:00:00Z 2024-03-22T11:00:00Z output.mp4 --api-token YOUR_API_TOKEN

# Using device name
safie-mediafile --name "Camera Name" 2024-03-22T10:00:00Z 2024-03-22T11:00:00Z output.mp4 --api-token YOUR_API_TOKEN
```

You can also set the API token using the `SAFIE_TOKEN` environment variable:

```bash
# Set API token as an environment variable
export SAFIE_TOKEN=YOUR_API_TOKEN
safie-mediafile --serial 201055433 2024-03-22T10:00:00Z 2024-03-22T11:00:00Z output.mp4
```

Note: The command-line interface is only available if you install the package with the `cli` extra.

### Python API

```python
import asyncio
from datetime import datetime
from safie_mediafile import find_device_id, create_and_download_mediafile

async def download_media():
    # Set up time (ISO 8601 format)
    start = datetime.fromisoformat("2024-03-22T10:00:00+09:00")
    end = datetime.fromisoformat("2024-03-22T11:00:00+09:00")

    # Get device ID (search by serial number or name)
    device_id = await find_device_id(
        api_token="your_api_token",
        serial="201055433",  # or name="Camera Name" (use either one)
    )

    # Create and download media file
    with open("output.mp4", "wb") as f:
        await create_and_download_mediafile(
            device_id=device_id,
            start_time=start,
            end_time=end,
            file=f,  # file object opened in binary mode
            api_token="your_api_token",
        )

if __name__ == "__main__":
    asyncio.run(download_media())
```

## Requirements

### Core Library
- Python 3.8 or later
- `httpx` for HTTP requests

### CLI Tool (Optional)
- `click` for command-line interface

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/example/safie-mediafile.git
cd safie-mediafile

# Install development dependencies
pip install -e ".[dev,cli]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=safie_mediafile tests/
```

### Code Quality

```bash
# Run linter
ruff check .

# Run type checker
mypy safie_mediafile
```

## Releasing

This package uses GitHub Actions to automatically build and publish to TestPyPI when a new release is created.

### Release Process

1. Update the version in `pyproject.toml`
2. Create and push a new tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
3. Create a new release on GitHub using the tag
4. The GitHub Actions workflow will automatically build and publish to TestPyPI

### TestPyPI

To install the package from TestPyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ safie-mediafile
```

## License

MIT License
