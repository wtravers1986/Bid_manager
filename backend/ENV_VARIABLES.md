# Environment Variables Reference

This document lists all environment variables used by the chatbot application.

## Required Variables

### Gemini Configuration (via Proxy)
- **`ENDPOINT`** (Required)
  - Description: The API endpoint URL for the Gemini proxy service
  - Example: `https://genai-sharedservice-emea.pwc.com`
  - Note: This is the base URL of your LiteLLM proxy or API gateway

- **`API_KEY`** (Required)
  - Description: API key for authenticating with the endpoint
  - Example: `sk-ufuH2c5myyTx3hPOpOrMZg`
  - Note: Keep this secure and never commit it to version control

- **`DEPLOYMENT_NAME`** (Required)
  - Description: The model deployment name to use
  - Example: `vertex_ai.gemini-3-pro-preview`
  - Note: This is the model identifier used by your proxy service

## Optional Variables

### Gemini Configuration
- **`EMBEDDING_DEPLOYMENT`** (Optional)
  - Description: Embedding model deployment name (if using embeddings)
  - Example: `vertex_ai.gemini-3-embedding`
  - Note: Currently not used in the chatbot, but available for future use

### Application Settings
- **`APP_NAME`** (Optional, Default: `Chatbot`)
  - Description: Application name

- **`ENVIRONMENT`** (Optional, Default: `development`)
  - Description: Environment name (`development` or `production`)

- **`DEBUG`** (Optional, Default: `false`)
  - Description: Enable debug mode
  - Values: `true` or `false`

- **`API_HOST`** (Optional, Default: `0.0.0.0`)
  - Description: Host to bind the API server

- **`API_PORT`** (Optional, Default: `8000`)
  - Description: Port for the API server

- **`CORS_ORIGINS`** (Optional, Default: `http://localhost:3000`)
  - Description: Comma-separated list of allowed CORS origins
  - Example: `http://localhost:3000,https://example.com`

- **`LOG_LEVEL`** (Optional, Default: `INFO`)
  - Description: Logging level
  - Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### AI Configuration
- **`TEMPERATURE`** (Optional, Default: `0.7`)
  - Description: Sampling temperature for AI responses (0.0 to 1.0)
  - Higher values = more creative/random responses
  - Lower values = more focused/deterministic responses

- **`MAX_TOKENS`** (Optional, Default: `2000`)
  - Description: Maximum number of tokens in AI response

## Example .env File

```env
# Required: Gemini Configuration (via Proxy)
ENDPOINT=https://genai-sharedservice-emea.pwc.com
API_KEY=sk-ufuH2c5myyTx3hPOpOrMZg
DEPLOYMENT_NAME=vertex_ai.gemini-3-pro-preview
EMBEDDING_DEPLOYMENT=vertex_ai.gemini-3-embedding

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

# Logging
LOG_LEVEL=INFO
```

## Notes

- All environment variable names are case-insensitive (Pydantic Settings handles this)
- Variables can be set in a `.env` file in the `backend/` directory
- Variables can also be set as system environment variables
- The `.env` file should not be committed to version control (add it to `.gitignore`)
- **Security**: Never commit API keys or sensitive credentials to version control
