# WebP to JPEG Converter

A web-based application for converting WebP images to JPEG format with support for batch processing and archive files.

**Note:** This project was developed with AI assistance (GitHub Copilot).

## Features

- Convert single or multiple WebP files to JPEG
- Support for archive files (ZIP, RAR, 7Z)
- Batch processing with automatic ZIP packaging
- Drag and drop file upload
- 100% JPEG quality output
- Modern and responsive UI
- No file count limits
- Handles images with transparency (converts to white background)

## Requirements

- Python 3.7+
- Flask
- Pillow (PIL)
- rarfile
- py7zr

## Installation

1. Clone or download this repository

2. Install the required dependencies:

```bash
pip install flask pillow rarfile py7zr
```

## Usage

1. Start the Flask application:

```bash
python "from flask import Flask, render_template.py"
```

2. Open your web browser and navigate to:

```
http://127.0.0.1:5000
```

3. Upload your files:
   - Drag and drop WebP files directly onto the upload area
   - Click to select individual WebP files
   - Upload archive files (ZIP, RAR, or 7Z) containing WebP images
   - Mix different file types in a single upload

4. Click "Convert & Download" to process the files

5. Download results:
   - Single file: Downloads as a JPEG file
   - Multiple files: Downloads as a ZIP archive

## Supported Formats

### Input

- WebP image files (.webp)
- ZIP archives (.zip)
- RAR archives (.rar)
- 7-Zip archives (.7z)

### Output

- JPEG images (.jpg) at 100% quality
- ZIP archive for batch conversions

## Configuration

You can modify the following settings in the main Python file:

- `JPEG_QUALITY`: Set JPEG output quality (default: 100)
- `MAX_UPLOAD_SIZE`: Maximum upload size in bytes (default: 500 MB)

## Technical Details

- Images with transparency (RGBA, LA, P modes) are converted to RGB with a white background
- Archive files are processed in memory without creating temporary files
- Maximum upload size is configurable (default 500 MB)
- Uses PIL/Pillow for image processing
- Supports nested folders within archives

## Browser Compatibility

- Modern browsers with JavaScript enabled
- Drag and drop support requires HTML5
- Tested on Chrome, Firefox, Edge, and Safari

## Project Structure

```
conversor/
├── from flask import Flask, render_template.py  # Main application file
├── templates/
│   └── index.html                               # Frontend interface
└── README.md                                    # This file
```

## Error Handling

- Invalid file formats are automatically filtered
- Corrupted images are skipped with error logging
- Failed conversions don't interrupt batch processing
- User-friendly error messages in the interface

## Performance Notes

- Batch processing of 300+ files is supported
- Processing time depends on image size and quantity
- Archive extraction happens in memory for better performance
- Large batches may take several minutes to process

## License

This project is provided as-is for personal and commercial use.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Troubleshooting

### Files not converting

- Ensure files are valid WebP format
- Check that archive files are not password-protected
- Verify file size is under the upload limit

### Upload fails

- Increase `MAX_UPLOAD_SIZE` for larger batches
- Try uploading files in smaller batches
- Ensure sufficient disk space and memory

### Archive extraction errors

- Ensure archive files are not corrupted
- For RAR files, ensure UnRAR is installed on your system
- Try extracting manually to verify archive integrity
