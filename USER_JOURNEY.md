# User Journey - AI Document Cleanup Tool

## Overzicht

Deze applicatie helpt gebruikers om **meerdere documenten te consolideren tot één geïntegreerd document** met behulp van AI. Het proces combineert automatische analyse met menselijke controle, zodat gebruikers de volledige controle behouden over het eindresultaat.

### Hoofdfunctionaliteiten

1. **Document Indexering**: PDF/DOCX bestanden worden geïndexeerd voor semantische zoekopdrachten
2. **Structure Analyse**: AI analyseert documentstructuren en genereert een geïntegreerde inhoudsopgave
3. **Paragraaf Selectie**: Gebruikers selecteren relevante paragrafen per sectie met AI-ondersteuning
4. **Document Generatie**: Het systeem genereert een professioneel DOCX document met alle geselecteerde content

### Gebruikersrollen

- **Process Owner**: Beheert sessies en geeft finale goedkeuring
- **Engineer/Reviewer**: Reviewt AI-voorstellen en selecteert content
- **Viewer**: Bekijkt gegenereerde documenten

## Complete User Workflow

```mermaid
flowchart TD
    Start([User Opens Application]) --> Access{Access Method}
    Access -->|Local| Local[localhost:8501]
    Access -->|Public via Ngrok| Public[ngrok URL]
    
    Local --> Home[Streamlit Home Page]
    Public --> Home
    
    Home --> ChooseTab{Choose Tab}
    
    ChooseTab -->|Index Documents| IndexFlow[Index Documents Tab]
    ChooseTab -->|Synthesis| SynthesisFlow[Synthesis Tab]
    ChooseTab -->|Search| SearchFlow[Search Tab]
    
    %% Index Flow
    IndexFlow --> CheckIndex{Documents<br/>Indexed?}
    CheckIndex -->|No| PlaceFiles[Place PDF/DOCX files<br/>in ./data folder]
    PlaceFiles --> ClickIndex[Click 'Index All Documents']
    ClickIndex --> ProcessIndex[System Processes:<br/>- Parse documents<br/>- LLM-based chunking<br/>- Generate embeddings<br/>- Store in vector DB]
    ProcessIndex --> IndexComplete[✅ Indexing Complete]
    CheckIndex -->|Yes| IndexComplete
    IndexComplete --> BackToHome[Return to Home]
    
    %% Synthesis Flow
    SynthesisFlow --> Step1[Step 1: Create Session]
    Step1 --> EnterName[Enter Session Name]
    EnterName --> SelectPDFs[Select PDF Files<br/>to Synthesize]
    SelectPDFs --> CreateSession[Click 'Create Session']
    CreateSession --> SessionCreated[✅ Session Created]
    
    SessionCreated --> Step2[Step 2: Analyze Structures]
    Step2 --> ClickAnalyze[Click 'Analyze Structures &<br/>Generate Inventory Table']
    ClickAnalyze --> AnalyzeProcess[System Analyzes:<br/>- Document structures<br/>- Headings & sections<br/>- AI generates unified TOC]
    AnalyzeProcess --> InventoryTable[Inventory Table Generated]
    
    InventoryTable --> Step3[Step 3: Review & Edit Inventory]
    Step3 --> EditTable{User Reviews Table}
    EditTable -->|Edit Needed| ModifyTable[User Modifies:<br/>- Add/remove sections<br/>- Change titles<br/>- Adjust hierarchy levels<br/>- Reorder sections]
    ModifyTable --> SaveTable[Click 'Save Inventory Table']
    EditTable -->|OK| SaveTable
    SaveTable --> TableSaved[✅ Table Saved]
    
    TableSaved --> Step4[Step 4: Review Paragraphs by Section]
    Step4 --> ForEachSection{For Each Section}
    ForEachSection -->|Next Section| ClickFind[Click 'Find Paragraphs<br/>for Section']
    ClickFind --> FindProcess[System Finds:<br/>- Vector search for candidates<br/>- LLM validates relevance<br/>- Shows full paragraphs]
    FindProcess --> ReviewParas[User Reviews Paragraphs:<br/>- Reads content<br/>- Checks relevance score<br/>- Views source info]
    ReviewParas --> SelectParas[User Selects Paragraphs<br/>via checkboxes]
    SelectParas --> SaveParas[Click 'Save Paragraph Selections']
    SaveParas --> ForEachSection
    
    ForEachSection -->|All Sections Done| Step5[Step 5: Generate Document]
    Step5 --> ClickGenerate[Click 'Generate Final Document']
    ClickGenerate --> GenerateProcess[System Generates:<br/>- Collects selected paragraphs<br/>- Creates DOCX structure<br/>- Adds headings & formatting<br/>- Includes source references]
    GenerateProcess --> DocReady[✅ Document Generated]
    
    DocReady --> Download[Click 'Download DOCX Document']
    Download --> ReviewDoc[User Reviews Document<br/>in Word/Viewer]
    ReviewDoc --> Satisfied{Document OK?}
    Satisfied -->|No| BackToEdit[Go Back to Edit Sections]
    BackToEdit --> Step4
    Satisfied -->|Yes| Complete[✅ Process Complete]
    
    %% Search Flow
    SearchFlow --> EnterQuery[Enter Search Query]
    EnterQuery --> ClickSearch[Click Search]
    ClickSearch --> SearchProcess[Vector Search Finds:<br/>- Relevant chunks<br/>- Source documents<br/>- Page numbers]
    SearchProcess --> DisplayResults[Display Results with:<br/>- Content preview<br/>- Relevance scores<br/>- Source information]
    DisplayResults --> BackToHome
    
    BackToHome --> ChooseTab
    
    style Start fill:#e1f5ff
    style Complete fill:#c8e6c9
    style IndexComplete fill:#c8e6c9
    style DocReady fill:#c8e6c9
    style SessionCreated fill:#fff9c4
    style TableSaved fill:#fff9c4
    style ProcessIndex fill:#ffccbc
    style AnalyzeProcess fill:#ffccbc
    style FindProcess fill:#ffccbc
    style GenerateProcess fill:#ffccbc
    style SearchProcess fill:#ffccbc
```

## System Architecture from User Perspective

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Streamlit Web Interface<br/>localhost:8501 or ngrok URL]
    end
    
    subgraph "User Actions"
        Upload[Upload/Select Documents]
        Create[Create Synthesis Session]
        Review[Review & Edit Content]
        Generate[Generate Final Document]
    end
    
    subgraph "Backend API Layer"
        API[FastAPI Backend<br/>localhost:8000]
        Sessions[Session Management]
        Documents[Document Processing]
        Analysis[AI Analysis]
        Synthesis[Document Synthesis]
    end
    
    subgraph "AI Services"
        OpenAI[Azure OpenAI<br/>GPT-4 & Embeddings]
        VectorStore[Local HNSW Vector Store<br/>Semantic Search]
    end
    
    subgraph "Data Storage"
        DB[(PostgreSQL<br/>Sessions & Metadata)]
        Redis[(Redis<br/>Cache)]
        Files[File System<br/>PDF/DOCX Storage]
    end
    
    UI --> Upload
    UI --> Create
    UI --> Review
    UI --> Generate
    
    Upload --> API
    Create --> API
    Review --> API
    Generate --> API
    
    API --> Sessions
    API --> Documents
    API --> Analysis
    API --> Synthesis
    
    Documents --> OpenAI
    Analysis --> OpenAI
    Synthesis --> OpenAI
    
    Documents --> VectorStore
    Analysis --> VectorStore
    Synthesis --> VectorStore
    
    Sessions --> DB
    Documents --> DB
    Documents --> Files
    
    API --> Redis
    API --> DB
    
    style UI fill:#e3f2fd
    style API fill:#fff3e0
    style OpenAI fill:#f3e5f5
    style VectorStore fill:#f3e5f5
    style DB fill:#e8f5e9
    style Redis fill:#e8f5e9
    style Files fill:#e8f5e9
```

## Document Processing Pipeline

```mermaid
flowchart LR
    A[User Places PDFs<br/>in ./data folder] --> B[Click 'Index Documents']
    B --> C[Document Parser<br/>Extract Text & Structure]
    C --> D[LLM-Based Chunking<br/>Logical Paragraph Boundaries]
    D --> E[Generate Embeddings<br/>Azure OpenAI]
    E --> F[Store in Vector DB<br/>HNSW Index]
    F --> G[✅ Documents Indexed<br/>Ready for Search]
    
    style A fill:#e1f5ff
    style G fill:#c8e6c9
    style C fill:#fff9c4
    style D fill:#fff9c4
    style E fill:#ffccbc
    style F fill:#ffccbc
```

## Synthesis Workflow Detail

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Streamlit UI
    participant API as Backend API
    participant AI as Azure OpenAI
    participant VS as Vector Store
    participant DB as PostgreSQL
    
    U->>UI: Create Session (Select PDFs)
    UI->>API: POST /sessions
    API->>DB: Store Session
    DB-->>API: Session ID
    API-->>UI: Session Created
    
    U->>UI: Analyze Structures
    UI->>API: POST /synthesis/analyze
    API->>API: Parse All Documents
    API->>AI: Analyze Structures (GPT-4)
    AI-->>API: Unified TOC
    API->>DB: Store Inventory Table
    API-->>UI: Display Table
    
    U->>UI: Edit & Save Table
    UI->>API: PUT /synthesis/inventory
    API->>DB: Update Table
    API-->>UI: Saved
    
    loop For Each Section
        U->>UI: Find Paragraphs
        UI->>API: POST /synthesis/find-paragraphs
        API->>VS: Vector Search
        VS-->>API: Candidate Paragraphs
        API->>AI: Validate Relevance (GPT-4)
        AI-->>API: Filtered Paragraphs
        API-->>UI: Display Paragraphs
        
        U->>UI: Select Paragraphs
        UI->>API: PUT /synthesis/select-paragraphs
        API->>DB: Store Selections
    end
    
    U->>UI: Generate Document
    UI->>API: POST /synthesis/generate
    API->>DB: Get All Selections
    API->>API: Build DOCX Structure
    API->>Files: Save DOCX
    API-->>UI: Download Link
    
    U->>UI: Download Document
    UI->>Files: Download DOCX
    Files-->>U: Document File
```

## Decision Points & User Choices

```mermaid
flowchart TD
    Start([User Starts]) --> HasDocs{Has Documents<br/>in ./data?}
    HasDocs -->|No| AddDocs[Add PDF/DOCX files]
    AddDocs --> Indexed{Indexed?}
    HasDocs -->|Yes| Indexed
    
    Indexed -->|No| Index[Index Documents First]
    Index --> Indexed
    Indexed -->|Yes| CreateSession[Create Session]
    
    CreateSession --> Analyze[Analyze Structures]
    Analyze --> ReviewTable{Table OK?}
    ReviewTable -->|No| EditTable[Edit Inventory Table]
    EditTable --> ReviewTable
    ReviewTable -->|Yes| FindParas[Find Paragraphs]
    
    FindParas --> ReviewParas{Paragraphs<br/>Selected?}
    ReviewParas -->|No| FindParas
    ReviewParas -->|Yes| AllSections{All Sections<br/>Done?}
    AllSections -->|No| FindParas
    AllSections -->|Yes| Generate[Generate Document]
    
    Generate --> ReviewDoc{Document<br/>OK?}
    ReviewDoc -->|No| EditAgain[Edit Sections]
    EditAgain --> FindParas
    ReviewDoc -->|Yes| Done([✅ Complete])
    
    style Start fill:#e1f5ff
    style Done fill:#c8e6c9
    style ReviewTable fill:#fff9c4
    style ReviewParas fill:#fff9c4
    style ReviewDoc fill:#fff9c4
```

## Key User Interactions

```mermaid
graph TB
    subgraph "User Interface Elements"
        Tabs[Tab Navigation:<br/>- Index Documents<br/>- Synthesis<br/>- Search]
        Forms[Form Inputs:<br/>- Session Name<br/>- PDF Selection<br/>- Table Editing]
        Buttons[Action Buttons:<br/>- Index All<br/>- Analyze<br/>- Find Paragraphs<br/>- Generate]
        Displays[Information Displays:<br/>- Progress Messages<br/>- Tables<br/>- Paragraph Lists<br/>- Download Links]
    end
    
    subgraph "User Decisions"
        SelectPDFs[Which PDFs to Synthesize?]
        EditTable[How to Structure Document?]
        ChooseParas[Which Paragraphs to Include?]
        FinalReview[Is Output Acceptable?]
    end
    
    subgraph "System Responses"
        ProcessStatus[Processing Status Updates]
        AIResults[AI-Generated Content]
        SearchResults[Search Results]
        FinalDoc[Generated DOCX File]
    end
    
    Tabs --> SelectPDFs
    Forms --> EditTable
    Buttons --> ChooseParas
    Displays --> FinalReview
    
    SelectPDFs --> ProcessStatus
    EditTable --> AIResults
    ChooseParas --> SearchResults
    FinalReview --> FinalDoc
    
    style Tabs fill:#e3f2fd
    style Forms fill:#fff3e0
    style Buttons fill:#f3e5f5
    style Displays fill:#e8f5e9
```

