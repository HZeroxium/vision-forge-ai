# ai_service/main.py
import uvicorn
from ai_service.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("ai_service.main:app", host="0.0.0.0", port=8000, reload=True)
