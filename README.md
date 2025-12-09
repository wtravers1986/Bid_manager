# Chatbot with Vertex AI (Gemini)

A simple chatbot application with Vertex AI Gemini services in the backend.

## Features

- Clean chatbot interface built with React and Material-UI
- FastAPI backend with Vertex AI Gemini integration via LiteLLM
- Conversation history support
- Configurable temperature and max tokens

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Web framework
- **LiteLLM** - Vertex AI API wrapper
- **Google Cloud AI Platform** - Vertex AI SDK
- **Pydantic** - Data validation

### Frontend
- **React 18**
- **Material-UI (MUI)** - Component library
- **Axios** - HTTP client

## Setup & Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Cloud Project with Vertex AI API enabled
- Google Cloud credentials (service account key or Application Default Credentials)

### Backend Setup

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Google Cloud credentials**

   Option A: Using service account JSON file
   - Download a service account key from Google Cloud Console
   - Save it to a secure location
   - Set the path in your `.env` file

   Option B: Using Application Default Credentials (ADC)
   - Run: `gcloud auth application-default login`
   - This will use your user credentials

5. **Configure environment variables**
Create a `.env` file in the backend directory:
```env
# Vertex AI Configuration
VERTEX_AI_PROJECT=your-gcp-project-id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_CREDENTIALS_PATH=/path/to/service-account-key.json

# Application Settings
APP_NAME=Chatbot
ENVIRONMENT=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# AI Configuration
TEMPERATURE=0.7
MAX_TOKENS=2000
```

6. **Run the backend**
```bash
python -m app.main
# Or
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure environment variables (optional)**
Create a `.env` file in the frontend directory:
```env
REACT_APP_API_URL=http://localhost:8000
```

4. **Run the frontend**
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### POST `/api/v1/chat/`
Send a chat message and get an AI response.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Response:**
```json
{
  "message": "Hello! I'm doing well, thank you for asking...",
  "role": "assistant"
}
```

### GET `/health`
Health check endpoint.

### GET `/`
Root endpoint with API information.

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── chat.py          # Chat API endpoint
│   │   ├── core/
│   │   │   ├── config.py        # Configuration
│   │   │   └── logging.py       # Logging setup
│   │   ├── services/
│   │   │   └── openai_service.py # Vertex AI service
│   │   └── main.py              # FastAPI application
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js               # Main React component
│   │   └── index.js             # React entry point
│   └── package.json
└── README.md
```

## Usage

1. Start the backend server
2. Start the frontend development server
3. Open `http://localhost:3000` in your browser
4. Start chatting!

## Configuration

The chatbot can be configured through environment variables:

- `VERTEX_AI_PROJECT` - Google Cloud Project ID (required)
- `VERTEX_AI_LOCATION` - Vertex AI region (default: us-central1)
- `VERTEX_AI_CREDENTIALS_PATH` - Path to service account JSON file (optional if using ADC)
- `TEMPERATURE` - Sampling temperature (0-1, default: 0.7)
- `MAX_TOKENS` - Maximum tokens in response (default: 2000)

## Model

The chatbot uses **Gemini 3 Pro Preview** (`vertex_ai/gemini-3-pro-preview`) via Vertex AI.

## License

Proprietary - Internal use only
