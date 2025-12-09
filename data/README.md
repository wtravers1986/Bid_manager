# Data Folder

This folder contains the source documents that will be processed by the AI Lifting Document Cleanup Tool.

## Structure

```
data/
├── source/          # Documents uploaded via API (organized by session)
│   └── session_1/   # Session-specific subdirectories
├── output/          # Generated consolidated documents
└── archive/         # Archived old documents
```

## Adding Documents

### Option 1: Place files directly in data folder (root level)

Place your PDF or DOCX files directly in this `data/` folder (not in subdirectories).

Then use the API endpoint to scan and import them:
```
POST /api/v1/documents/scan-data-folder/{session_id}
```

This will:
- Scan the data folder for PDF/DOCX files
- Import them into the specified session
- Create database records for each file

### Option 2: Upload via API

Use the upload endpoint:
```
POST /api/v1/documents/upload/{session_id}
```

Files uploaded via API will be stored in `data/source/session_{session_id}/`

## Supported Formats

- PDF (`.pdf`)
- Word Documents (`.docx`, `.doc`)

## Notes

- Files placed directly in the `data/` folder root will be scanned by the scan endpoint
- Files are not moved or deleted during scanning - they remain in place
- The scan endpoint will skip files that are already imported in the session
- Maximum file size: 50MB (configurable)

