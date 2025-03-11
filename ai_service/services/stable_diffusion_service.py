# ai_service/services/stable_diffusion_service.py
from io import BytesIO
from fastapi import HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from ai_service.core.pipeline_manager import pipeline_manager


class StableDiffusionService:
    def generate_image(self, prompt: str):
        try:
            pipe = pipeline_manager.get_stable_diffusion()
            result = pipe(prompt)
            image = result.images[0]
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
