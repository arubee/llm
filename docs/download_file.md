# Download File Utility

A Python script to download files from URLs and automatically extract zip archives.

## Features

- Downloads files from any public URL
- Automatically detects and extracts zip files
- Creates necessary directories if they don't exist
- Updates status before and after download
- Command-line interface user input
- Error handling

## Pre-requisites

- Python installed
- uv for package manager

## Installation

1. create virtual environment
```
uv venv
```
2. Install the required package:
```
uv add requests
```

## Usage

### Command Line

```bash
python download_file.py <url> [--output_dir OUTPUT_DIR]
```

#### Arguments

- `url` (required): The URL of the file to download
- `--output_dir` (optional): Directory to save the downloaded file (default: 'companydata')

#### Example

```bash
# Download and extract a zip file
python download_file.py https://example.com/data.zip

# Specify custom output directory
python download_file.py https://example.com/data.zip --output_dir my_data
```
## Function Reference

### `download_and_unzip(url, output_dir='.')`

Downloads a file from a URL and extracts it if it's a zip file.

**Parameters:**
- `url` (str): The URL of the file to download
- `output_dir` (str): Directory to save the file (default: current directory)

**Returns:**
- str: Path to the downloaded file or the directory where it was extracted
- None: If download fails

## Error Handling

The script handles the following errors:
- Network connectivity issues
- Invalid URLs
- Permission errors when writing files
- Corrupt zip files

## Notes

- For zip files, the original zip file is deleted after extraction
- The script creates necessary directories if they don't exist
- Progress is shown during file download
- The script is compatible with both Python 3.6+ and 3.7+
