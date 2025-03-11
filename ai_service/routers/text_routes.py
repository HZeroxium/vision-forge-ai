# ai_service/routers/text_routes.py
from fastapi import APIRouter
from ai_service.schemas.text_schemas import TextPrompt
from ai_service.services.text_generation_service import TextGenerationService

router = APIRouter()
txt_service = TextGenerationService()


@router.post("/generate-text")
def generate_text(req: TextPrompt):
    result = txt_service.generate_text(req.prompt)
    return {"generated_text": result}
