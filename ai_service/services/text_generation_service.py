# ai_service/services/text_generation_service.py
from fastapi import HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from ai_service.core.pipeline_manager import pipeline_manager


class TextGenerationService:
    def generate_text(self, prompt: str) -> str:
        try:
            text_pipeline = pipeline_manager.get_text_generation()
            output = text_pipeline(prompt, max_length=50)
            return output[0]["generated_text"]
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
