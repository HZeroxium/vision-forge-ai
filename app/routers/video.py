# app/routers/video.py
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/create")
async def create_video():
    raise HTTPException(status_code=500, detail="Video generation not implemented yet")
