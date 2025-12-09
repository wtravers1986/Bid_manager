# Indexing Documents to Local HNSW Vector Store

This guide explains how to index documents from the `data/` folder into a local HNSW (Hierarchical Navigable Small World) vector store for semantic search.

## Overview

The indexing process:
1. **Scans** the `data/` folder for PDF/DOCX files
2. **Parses** each document to extract text
3. **Chunks** the text into smaller pieces (~1000 chars with 200 char overlap)
4. **Generates embeddings** using Azure OpenAI (text-embedding-ada-002)
5. **Indexes** all chunks in local HNSW vector store (stored in `data/vector_index.bin`)

## Prerequisites

1. **Azure OpenAI** configured (already done in `env.template`)
   - Embeddings are generated using Azure OpenAI
   - No Azure AI Search needed - everything is local!

2. **Documents** placed in the `data/` folder (root level)

## Step 1: Place Documents

Place your PDF or DOCX files directly in the `data/` folder:

```
data/
├── document1.pdf
├── document2.docx
└── document3.pdf
```

## Step 2: View Vector Store Schema (Optional)

View the vector store configuration:

```bash
GET /api/v1/documents/index-schema
```

This returns the HNSW configuration and statistics.

## Step 3: Index Documents

Trigger the indexing process:

```bash
POST /api/v1/documents/index-data-folder?session_id=1
```

**Parameters:**
- `session_id` (optional): Associate documents with a cleanup session

**Response:**
```json
{
  "success": true,
  "message": "Processed 3 documents, indexed 45 chunks",
  "processed": 3,
  "failed": 0,
  "indexed_chunks": 45,
  "failed_documents": []
}
```

## What Happens During Indexing

1. **Vector Store Initialization**: Loads or creates local HNSW index
2. **Document Processing**: For each document:
   - Parses the document (PDF/DOCX)
   - Extracts text and metadata
   - Splits into chunks
   - Generates embeddings (batch of 16 at a time)
   - Adds vectors to HNSW index
3. **Persistence**: Saves index to `data/vector_index.bin` and metadata to `data/vector_metadata.json`

## Vector Store Structure

The HNSW index stores:

- **Vectors**: 1536-dimensional embeddings (ada-002)
- **Metadata** for each vector:
  - `id`: Unique identifier
  - `content`: The chunk text
  - `filename`: Source document filename
  - `page_number`: Page number in source document
  - `section_title`: Section/heading title
  - `chunk_index`: Order within document
  - `session_id`: Associated session ID
  - `file_type`: Document type (pdf/docx)
  - `page_count`: Total pages in document

## Using the Vector Store

After indexing, you can search using:

```bash
POST /api/v1/search/search
```

**Request:**
```json
{
  "query": "What are the safety requirements for lifting operations?",
  "top_k": 10,
  "filters": {
    "filename": "safety_manual.pdf"
  }
}
```

**Response:**
```json
{
  "query": "What are the safety requirements...",
  "total_results": 10,
  "results": [
    {
      "id": "...",
      "content": "...",
      "filename": "safety_manual.pdf",
      "page_number": 5,
      "score": 0.92,
      "distance": 0.08
    }
  ]
}
```

You can also:
- **Get stats**: `GET /api/v1/search/stats`
- **Clear index**: `POST /api/v1/search/clear-index`

## Troubleshooting

### Index Creation Fails
- Check that the `data/` directory is writable
- Verify disk space is available
- Check file permissions

### Embedding Generation Fails
- Verify Azure OpenAI credentials
- Check that the embedding deployment exists: `openai-nsoai-text-embedding-ada-002`
- Check API quotas/limits

### No Documents Found
- Ensure files are in the `data/` folder root (not subdirectories)
- Check file extensions: `.pdf`, `.docx`, `.doc`
- Verify file permissions

### Processing Errors
- Check logs for specific error messages
- Verify documents are not corrupted
- Ensure documents are readable (not password-protected)

## Performance Notes

- **Embedding Generation**: ~16 chunks per batch (to avoid rate limits)
- **Indexing**: All vectors added to HNSW index
- **Processing Time**: ~2-5 seconds per document (depending on size)
- **Large Documents**: May take longer, consider splitting very large files
- **Index Size**: HNSW index grows with number of vectors (~1-2MB per 1000 vectors)

## Storage

The vector store is saved locally:
- **Index file**: `data/vector_index.bin` (HNSW graph structure)
- **Metadata file**: `data/vector_metadata.json` (chunk metadata and mappings)

Both files are automatically loaded on startup.

## Re-indexing

To re-index documents:
1. Clear the index: `POST /api/v1/search/clear-index`
2. Run the indexing process again: `POST /api/v1/documents/index-data-folder`

Note: Re-indexing will create duplicate entries if the index already contains the documents. Consider clearing the index first.

