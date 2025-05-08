# Vision Forge AI

A comprehensive AI media generation platform built with FastAPI that creates scientific educational content through text, images, audio, and videos.

## Features

- **Scientific Script Generation**: Create educational scripts using RAG (Retrieval-Augmented Generation)
- **AI Image Generation**: Convert scripts into descriptive image prompts
- **Text-to-Speech**: Convert scripts into audio narrations using OpenAI's TTS
- **Motion Video Creation**: Create dynamic videos from images and audio
- **Multi-voice Support**: Create videos with multiple voice narrations
- **Storage Management**: Integration with Digital Ocean Spaces for media storage

## System Requirements

- Python 3.9+
- FFmpeg (required for video processing)
- OpenAI API key
- Digital Ocean Spaces account (for storage)
- Pinecone account (for vector embeddings)
- Tavily API key (for RAG enhancement)
- CUDA-compatible GPU (recommended for better performance)

## Installation

### 1. Clone the repository

```bash
git clone [repository-url]
cd vision-forge-ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows**:

```bash
.venv\Scripts\activate
```

**Linux/macOS**:

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Copy the example environment file and update it with your credentials:

```bash
cp .env.example .env
```

Then edit the `.env` file with your API keys and configuration.

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

The server will be available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## API Documentation

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Key Endpoints

- `/api/v1/text/script/create` - Generate scientific scripts
- `/api/v1/text/prompts/create` - Generate image prompts from scripts
- `/api/v1/image/generate` - Generate images from prompts
- `/api/v1/audio/create` - Convert text to speech
- `/api/v1/video/create` - Create videos from images and audio
- `/api/v1/storage/upload` - Upload files to storage

## External Services

This project relies on several external services:

- **OpenAI API**: For GPT-4 based script generation and text-to-speech
- **Pinecone**: Vector database for embedding storage and similarity search
- **Digital Ocean Spaces**: Object storage for media files
- **Tavily**: For enhanced information retrieval

## Logging

The application uses a configured logger with colored console output and file logging. Logs are stored in `app.log` with rotation.
