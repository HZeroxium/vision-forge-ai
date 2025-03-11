# ai_service/routers/image_routes.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ai_service.schemas.image_schemas import ImagePrompt
from ai_service.services.stable_diffusion_service import StableDiffusionService

router = APIRouter()
sd_service = StableDiffusionService()


@router.post("/generate-image")
def generate_image(req: ImagePrompt):
    buffer = sd_service.generate_image(req.prompt)
    return {"message": "Image generated", "length": len(buffer.getvalue())}


@router.post("/generate-image-binary")
def generate_image_binary(req: ImagePrompt):
    buffer = sd_service.generate_image(req.prompt)
    return StreamingResponse(buffer, media_type="image/png")
