from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uuid, pathlib, tempfile
import asyncio

app = FastAPI()


class Gen3DRequest(BaseModel):
    prompt: str = Field(..., min_length=4, description="Object prompt (e.g. 'coffee cup')")
    lod: int = Field(ge=0, le=2, default=1)
    job_id: str


class Gen3DResponse(BaseModel):
    glb_url: str | None          # None ⇒ model missing
    fallback: bool = False       # True ⇒ pipeline failed
    error: str | None = None     # human-readable reason


# Заглушка для симуляции pipeline
async def run_pipeline(req: Gen3DRequest):
    # Симуляция длительной обработки
    await asyncio.sleep(2)
    
    # Эта заглушка всегда возвращает None для имитации отсутствия mesh
    # В реальной реализации тут будет DreamGaussian или подобная библиотека
    return None


@app.post("/generate3d", response_model=Gen3DResponse)
async def generate3d(req: Gen3DRequest):
    """
    Main 3-D pipeline entrypoint.
    Raises HTTP 422 on vague prompt instead of producing placeholder geometry.
    """
    # 1. Basic prompt sanity (no generic 'object', '3d', etc.)
    banned = {"object", "thing", "stuff", "3d"}
    if any(w.lower() in banned for w in req.prompt.split()):
        raise HTTPException(
            status_code=422,
            detail="3D_GENERATION_FAILED: Prompt too vague for reliable mesh"
        )

    try:
        # 2. Shap-E → DreamGaussian → GS-GS
        mesh_path = await run_pipeline(req)
    except Exception as e:
        # Hard failure ⇒ report, but **no** placeholder cube or image
        return Gen3DResponse(
            glb_url=None,
            fallback=True,
            error=f"PIPELINE_ERROR: {e}"
        )

    if mesh_path is None:        # pipeline returned nothing
        # Никогда не возвращаем изображение вместо mesh, только честную ошибку
        return Gen3DResponse(
            glb_url=None,
            fallback=True,
            error="NO_MESH: 3D generation failed, no mesh was produced."
        )

    return Gen3DResponse(glb_url=str(mesh_path), fallback=False)
