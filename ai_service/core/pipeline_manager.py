# ai_service/core/pipeline_manager.py
import torch
from diffusers import StableDiffusionPipeline
from transformers import pipeline
from .config import settings


class PipelineManager:
    def __init__(self):
        self._sd_pipeline = None
        self._text_pipeline = None

    def get_stable_diffusion(self) -> StableDiffusionPipeline:
        if not self._sd_pipeline:
            model_id = settings.MODEL_ID
            if torch.cuda.is_available() and settings.CUDA_AVAILABLE:
                pipe = StableDiffusionPipeline.from_pretrained(
                    model_id, torch_dtype=torch.float16
                ).to("cuda")
            else:
                pipe = StableDiffusionPipeline.from_pretrained(model_id)
            self._sd_pipeline = pipe
        return self._sd_pipeline

    def get_text_generation(self):
        if not self._text_pipeline:
            model_id = settings.TEXT_MODEL_ID
            self._text_pipeline = pipeline("text-generation", model=model_id)
        return self._text_pipeline


pipeline_manager = PipelineManager()
