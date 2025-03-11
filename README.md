# Vision Forge AI

AI image generation service built with FastAPI.

## System Requirements

- Python 3.9+
- CUDA-compatible GPU (recommended)

## Installation

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the virtual environment

**Windows**:

```bash
.venv\Scripts\activate
```

**Linux/MacOS**:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
uvicorn ai_service.main:app --reload
```

Server will be available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

API Documentation
Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/doc)
