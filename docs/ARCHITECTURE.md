# Architecture Documentation

## System Overview

De AI Lifting Document Cleanup Tool is een gedistribueerde applicatie die bestaat uit meerdere componenten die samenwerken om het document consolidatie proces te automatiseren.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          User Interface Layer                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  React Frontend (Material-UI)                               │   │
│  │  - Session Management                                        │   │
│  │  - Document Upload                                           │   │
│  │  - Review Interface                                          │   │
│  │  - Conflict Resolution                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
└───────────────────────────────┬───────────────────────────────────────┘
                                │ REST API / JSON
                                │
┌───────────────────────────────▼───────────────────────────────────────┐
│                      Application Layer (FastAPI)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  API Endpoints                   Business Logic Services             │
│  ┌─────────────────┐           ┌──────────────────────┐            │
│  │ Sessions API    │◄─────────►│ Document Parser      │            │
│  │ Documents API   │           │ - PDF Parser         │            │
│  │ Sections API    │           │ - DOCX Parser        │            │
│  │ Analysis API    │           │ - Chunking Engine    │            │
│  └─────────────────┘           └──────────────────────┘            │
│                                                                       │
│  AI Agent Orchestration                                              │
│  ┌────────────────────────────────────────────────────────┐         │
│  │ ┌─────────────────┐  ┌──────────────────┐            │         │
│  │ │ Contradiction   │  │ Summarization    │            │         │
│  │ │ Detection Agent │  │ Agent            │            │         │
│  │ └─────────────────┘  └──────────────────┘            │         │
│  │ ┌─────────────────┐  ┌──────────────────┐            │         │
│  │ │ Ranking Agent   │  │ Figure           │            │         │
│  │ │                 │  │ Suggestion Agent │            │         │
│  │ └─────────────────┘  └──────────────────┘            │         │
│  └────────────────────────────────────────────────────────┘         │
│                                                                       │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
┌─────────────────────┐ ┌──────────────┐  ┌──────────────────┐
│   PostgreSQL        │ │    Redis     │  │  Azure Services  │
│   Database          │ │   Cache +    │  │                  │
│   - Sessions        │ │   Celery     │  │ ┌──────────────┐ │
│   - Documents       │ │   Queue      │  │ │ Azure        │ │
│   - Chunks          │ │              │  │ │ OpenAI       │ │
│   - Reviews         │ │              │  │ │ (GPT-4)      │ │
│   - Conflicts       │ │              │  │ └──────────────┘ │
└─────────────────────┘ └──────────────┘  │ ┌──────────────┐ │
                                           │ │ Azure AI     │ │
                                           │ │ Search       │ │
                                           │ │ (Vector DB)  │ │
                                           │ └──────────────┘ │
                                           │ ┌──────────────┐ │
                                           │ │ Azure Blob   │ │
                                           │ │ Storage      │ │
                                           │ └──────────────┘ │
                                           └──────────────────┘
```

## Component Details

### 1. Frontend Layer (React)

**Technology Stack**:
- React 18 with functional components and hooks
- Material-UI (MUI) for UI components
- React Query for data fetching and caching
- React Router for navigation
- Axios for HTTP client

**Key Features**:
- Responsive design for desktop use
- Real-time updates for processing status
- Side-by-side diff view for conflict resolution
- Citation hover-over with source preview
- Drag-and-drop document upload

**Key Components**:
```
src/
├── components/
│   ├── SessionList.tsx
│   ├── DocumentUpload.tsx
│   ├── SectionReview.tsx
│   ├── ConflictResolution.tsx
│   ├── CitationViewer.tsx
│   └── FigureGallery.tsx
├── pages/
│   ├── HomePage.tsx
│   ├── SessionsPage.tsx
│   ├── ReviewPage.tsx
│   └── OutputPage.tsx
├── services/
│   ├── api.ts
│   └── websocket.ts
└── types/
    └── models.ts
```

### 2. Backend API Layer (FastAPI)

**Technology Stack**:
- FastAPI 0.109+ (async Python web framework)
- SQLAlchemy 2.0 with async support
- Pydantic v2 for data validation
- Celery for async task processing
- Python 3.11+

**API Endpoints**:

```
/api/v1/
├── sessions/
│   ├── POST   /                    # Create session
│   ├── GET    /                    # List sessions
│   ├── GET    /{id}               # Get session
│   ├── PATCH  /{id}               # Update session
│   └── DELETE /{id}               # Delete session
├── documents/
│   ├── POST   /upload/{session_id} # Upload document
│   ├── GET    /session/{session_id}# List documents
│   ├── GET    /{id}               # Get document
│   └── DELETE /{id}               # Delete document
├── sections/
│   ├── GET    /session/{session_id}# List sections
│   ├── GET    /{id}               # Get section
│   ├── PATCH  /{id}               # Update section
│   ├── GET    /{id}/candidates    # Get candidates
│   └── PATCH  /{id}/candidates/{candidate_id} # Review candidate
└── analysis/
    ├── POST   /section/{id}/detect-contradictions
    ├── POST   /section/{id}/generate-summary
    └── GET    /section/{id}/conflicts
```

**Architecture Patterns**:
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic separation
- **Dependency Injection**: FastAPI's built-in DI
- **Async/Await**: Non-blocking I/O throughout

### 3. Document Processing Pipeline

**Flow**:

```
1. Upload → 2. Parse → 3. Chunk → 4. Embed → 5. Index

┌──────────┐
│  Upload  │  User uploads PDF/DOCX
└────┬─────┘
     │
     ▼
┌──────────┐  ┌─────────────────────────────┐
│  Parse   │  │ - Extract text             │
│  Stage   │──│ - Extract figures/images   │
└────┬─────┘  │ - Extract metadata         │
     │        └─────────────────────────────┘
     ▼
┌──────────┐  ┌─────────────────────────────┐
│  Chunk   │  │ - Split into ~1000 char     │
│  Stage   │──│ - Overlap 200 chars         │
└────┬─────┘  │ - Preserve context          │
     │        └─────────────────────────────┘
     ▼
┌──────────┐  ┌─────────────────────────────┐
│  Embed   │  │ - Generate embeddings       │
│  Stage   │──│ - Batch processing (16)     │
└────┬─────┘  │ - 1536 dimensions (ada-002)│
     │        └─────────────────────────────┘
     ▼
┌──────────┐  ┌─────────────────────────────┐
│  Index   │  │ - Upload to Azure AI Search │
│  Stage   │──│ - HNSW algorithm            │
└──────────┘  │ - Hybrid search enabled     │
              └─────────────────────────────┘
```

**Parsers**:

- **PDFParser** (PyMuPDF/fitz)
  - Text extraction with layout preservation
  - Image extraction with min size filter
  - Caption detection heuristics
  - OCR support for scanned PDFs

- **DOCXParser** (python-docx)
  - Text extraction with heading detection
  - Table extraction
  - Image extraction from relationships
  - Style preservation

- **ChunkingEngine**
  - Sentence-boundary aware splitting
  - Configurable overlap
  - Section title tracking
  - Token counting

### 4. AI Agent System

**Base Architecture**:

```python
class BaseAgent(ABC):
    def __init__(self, openai_service):
        self.openai_service = openai_service

    @abstractmethod
    async def execute(self, **kwargs) -> AgentResult:
        pass
```

**Agent Types**:

#### ContradictionAgent
- **Purpose**: Detect conflicts between passages
- **Method**: Pairwise GPT-4 analysis
- **Output**: Conflict type, confidence, severity
- **Complexity**: O(n²) for n candidates

#### SummarizationAgent
- **Purpose**: Generate consolidated text
- **Method**: Multi-passage synthesis with citations
- **Output**: Summary, key points, citations map
- **Features**:
  - Maintains safety-critical info
  - Explicit contradiction noting
  - Source tracking

#### RankingAgent
- **Purpose**: Prioritize candidate passages
- **Method**: Multi-criteria evaluation
- **Criteria**:
  - Relevance to section
  - Completeness
  - Clarity
  - Technical accuracy
  - Recency

#### FigureSuggestionAgent
- **Purpose**: Match figures to text
- **Method**: Semantic similarity + GPT-4 relevance
- **Output**: Figure ID, placement, caption

### 5. Data Models

**Core Entities**:

```
CleanupSession
├── name, description, status
├── table_of_contents (JSON)
├── personas (JSON)
└── 1:N SourceDocument
    ├── filename, blob_path
    ├── file_type, page_count
    └── 1:N DocumentChunk
        ├── content, embedding
        └── vector_id

SessionSection
├── section_number, title
├── ai_draft, ai_confidence
├── final_content
└── 1:N SectionCandidate
    ├── chunk_id (FK)
    ├── relevance_score
    ├── is_selected
    └── reviewer_decision

ContentConflict
├── section_id (FK)
├── candidate_a_id, candidate_b_id
├── conflict_type, description
├── confidence, severity
└── is_resolved

OutputDocument
├── session_id (FK)
├── title, version
├── content_json
├── docx_path, pdf_path
└── source_document_ids (JSON)
```

**Relationships**:
- CleanupSession 1:N SourceDocument
- SourceDocument 1:N DocumentChunk
- SourceDocument 1:N DocumentFigure
- CleanupSession 1:N SessionSection
- SessionSection 1:N SectionCandidate
- SectionCandidate N:1 DocumentChunk
- SessionSection 1:N ContentConflict
- CleanupSession 1:N OutputDocument

### 6. Azure Services Integration

#### Azure OpenAI
- **Model**: GPT-4 (gpt-4 deployment)
- **Embedding**: text-embedding-ada-002
- **API Version**: 2024-02-15-preview
- **Usage**:
  - Text generation: Summaries, contradiction detection
  - Embeddings: Vector search
  - Classification: Ranking, relevance scoring

**Cost Optimization**:
- Batch embedding requests (16 at a time)
- Cache common queries
- Use temperature=0.2-0.3 for consistency
- Monitor token usage

#### Azure AI Search
- **Tier**: Standard or higher (for vector search)
- **Algorithm**: HNSW with cosine similarity
- **Index Schema**:
  ```json
  {
    "fields": [
      {"name": "id", "type": "Edm.String", "key": true},
      {"name": "content", "type": "Edm.String", "searchable": true},
      {"name": "content_vector", "type": "Collection(Edm.Single)",
       "dimensions": 1536, "searchable": true},
      {"name": "source_document_id", "type": "Edm.Int32", "filterable": true},
      {"name": "session_id", "type": "Edm.Int32", "filterable": true}
    ]
  }
  ```

**Search Types**:
- **Vector Search**: Semantic similarity via embeddings
- **Hybrid Search**: Combines keyword + vector
- **Filtered Search**: By session, document, date, etc.

#### Azure Blob Storage
- **Containers**:
  - `source-documents`: Original uploads
  - `output-documents`: Generated outputs
  - `archive-documents`: Old procedures (Phase 1 cleanup)

- **Access**:
  - Private containers (no public access)
  - SAS tokens for temporary access
  - Soft delete enabled (7 days)

- **Tiers**:
  - Hot: Active documents
  - Cool: Archive documents

### 7. Security Architecture

**Authentication & Authorization**:
- Azure AD integration for SSO
- Role-Based Access Control (RBAC)
  - Admin: Full access
  - Reviewer: Read + Write (no delete)
  - Viewer: Read only

**Data Security**:
- Encryption at rest (Azure default)
- Encryption in transit (HTTPS/TLS 1.2+)
- Secrets in Azure Key Vault
- No PII in logs

**Network Security**:
- Private endpoints for Azure services
- NSG rules for container communication
- WAF for frontend (optional)

### 8. Scalability & Performance

**Horizontal Scaling**:
- Backend: Auto-scale based on CPU/requests
- Database: Azure PostgreSQL Flexible Server with read replicas
- Search: Partition index by session

**Caching Strategy**:
- Redis for:
  - Session data
  - API response caching
  - Celery task queue

**Performance Targets**:
- API response time: < 500ms (p95)
- Document processing: < 2 min for 50-page PDF
- Vector search: < 200ms (p95)
- Summary generation: < 30s per section

**Bottlenecks & Mitigation**:
- GPT-4 rate limits → Retry with exponential backoff
- Embedding batch size → Process in parallel
- Database queries → Proper indexing + query optimization

## Deployment Architecture

### Development Environment
```
Docker Compose
├── postgres (container)
├── redis (container)
├── backend (container)
└── frontend (container)
```

### Production Environment (Azure)
```
Azure Container Apps
├── Backend Container App (auto-scale 1-10)
├── Frontend Container App (auto-scale 1-5)
├── Azure PostgreSQL Flexible Server
├── Azure Redis Cache
├── Azure OpenAI Service
├── Azure AI Search Service
└── Azure Blob Storage
```

## Monitoring & Observability

**Logging**:
- Structured JSON logging
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Correlation IDs for request tracking

**Metrics**:
- Request latency (p50, p95, p99)
- Error rates
- Document processing throughput
- Azure service costs

**Alerting**:
- High error rates (> 5%)
- Slow requests (> 2s)
- Service health failures
- Azure quota limits

**Tools**:
- Application Insights for APM
- Azure Monitor for infrastructure
- Custom dashboards for business metrics

## Future Enhancements

### Phase 2: Maintenance Flow
- Automated change detection
- Impact analysis for updates
- Scheduled review reminders
- Version comparison

### Performance Optimizations
- Implement GraphQL for flexible queries
- Add WebSocket support for real-time updates
- Implement client-side caching
- Optimize database queries with materialized views

### Feature Additions
- Multi-language support
- Advanced figure recognition (ML-based)
- Automated testing of procedures
- Integration with QHSE systems

---

**Document Version**: 1.0
**Last Updated**: November 2024
