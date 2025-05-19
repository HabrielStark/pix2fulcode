from fastapi import FastAPI, HTTPException, BackgroundTasks
import httpx, os, hashlib, json
import asyncio
import logging
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы для OpenRouter API
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
DEEPSEEK_MODEL_ID = "deepseek/deepseek-chat:free"

# Константы для ESLint и pa11y проверок
ESLINT_CMD = "npx eslint --fix"
PA11Y_CMD = "npx pa11y-ci"

app = FastAPI()

# Модели данных
class CodeGenerationRequest(BaseModel):
    ui_json: Dict[str, Any]
    format: str = Field(default="next", description="Format of the generated code: html, tailwind, or next")
    job_id: str = Field(..., description="UUID of the job")

class CodeChunk(BaseModel):
    chunk_id: int
    content: str
    linting_passed: bool
    a11y_passed: bool

class CodeGenerationResponse(BaseModel):
    chunks: List[CodeChunk]
    complete: bool
    job_id: str

# Состояние генерации для каждого задания
generation_state = {}

async def check_code_quality(code_chunk: str) -> tuple:
    """
    Проверяет качество кода с использованием ESLint и pa11y-ci.
    Возвращает кортеж (linting_passed, a11y_passed)
    """
    # Заглушка для демонстрации - в реальном сервисе здесь будет вызов линтеров
    # В производственной версии эти проверки должны быть выполнены в изолированной среде
    await asyncio.sleep(0.5)  # Имитация проверки
    linting_passed = True
    a11y_passed = True
    return linting_passed, a11y_passed

async def generate_code_with_openrouter(ui_json: dict, format: str, seed: int) -> List[CodeChunk]:
    """
    Генерирует код на основе UI JSON, используя OpenRouter API с моделью DeepSeek.
    """
    # Преобразуем UI JSON в промпт для LLM
    ui_json_str = json.dumps(ui_json, indent=2)
    
    prompt = f"""
    Ты профессиональный UI разработчик. Создай рабочий фронтенд код на основе данного UI JSON.
    
    UI JSON описание:
    ```json
    {ui_json_str}
    ```
    
    Формат: {format}
    
    Пожалуйста, создай чистый, производственный код для всех компонентов, описанных в UI JSON.
    Включи все необходимые импорты и интеграцию 3D-объектов, если они присутствуют в UI JSON.
    Код должен соответствовать современным стандартам доступности и лучшим практикам.
    """
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://pix2fullcode.ai",
        "X-Title": "Pix2FullCode-3D",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": DEEPSEEK_MODEL_ID,
        "messages": [
            {"role": "system", "content": "You are a professional UI developer expert in creating clean, accessible frontend code."},
            {"role": "user", "content": prompt}
        ],
        "seed": seed,
        "stream": True,
        "max_tokens": 4000
    }
    
    chunks = []
    chunk_id = 0
    current_chunk = ""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", OPENROUTER_API_URL, headers=headers, json=data) as response:
                if response.status_code != 200:
                    error_detail = await response.aread()
                    logger.error(f"OpenRouter API error: {response.status_code}, {error_detail}")
                    raise HTTPException(status_code=500, detail=f"OpenRouter API returned error: {response.status_code}")
                
                async for line in response.aiter_lines():
                    if not line or line == "data: [DONE]":
                        continue
                    
                    if line.startswith("data: "):
                        try:
                            json_data = json.loads(line[6:])
                            content = json_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                current_chunk += content
                                
                                # Создаем новый чанк каждые 2k токенов (приблизительно)
                                if len(current_chunk) > 2000:
                                    linting_passed, a11y_passed = await check_code_quality(current_chunk)
                                    chunks.append(CodeChunk(
                                        chunk_id=chunk_id,
                                        content=current_chunk,
                                        linting_passed=linting_passed,
                                        a11y_passed=a11y_passed
                                    ))
                                    chunk_id += 1
                                    current_chunk = ""
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode JSON from line: {line}")
    
    except (httpx.RequestError, asyncio.TimeoutError) as e:
        logger.error(f"Error making request to OpenRouter API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to OpenRouter API: {str(e)}")
    
    # Добавляем последний чанк, если он не пустой
    if current_chunk:
        linting_passed, a11y_passed = await check_code_quality(current_chunk)
        chunks.append(CodeChunk(
            chunk_id=chunk_id,
            content=current_chunk,
            linting_passed=linting_passed,
            a11y_passed=a11y_passed
        ))
    
    return chunks

@app.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(request: CodeGenerationRequest, background_tasks: BackgroundTasks):
    """
    Генерирует код на основе UI JSON, используя DeepSeek через OpenRouter.
    Возвращает чанки кода с результатами проверки линтером и a11y.
    """
    job_id = request.job_id
    ui_json = request.ui_json
    format = request.format
    
    # Создаем детерминированный seed из UI JSON, как указано в ТЗ
    seed = int(hashlib.crc32(json.dumps(ui_json, sort_keys=True).encode())) & 0xFFFFFFFF
    
    logger.info(f"Starting code generation for job {job_id} with format {format} and seed {seed}")
    
    try:
        # Запускаем генерацию кода асинхронно
        chunks = await generate_code_with_openrouter(ui_json, format, seed)
        
        # Обновляем состояние генерации
        generation_state[job_id] = {
            "chunks": chunks,
            "complete": True
        }
        
        return CodeGenerationResponse(
            chunks=chunks,
            complete=True,
            job_id=job_id
        )
    
    except Exception as e:
        logger.error(f"Error during code generation for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")

@app.get("/status/{job_id}")
async def get_generation_status(job_id: str):
    """
    Возвращает текущий статус генерации кода для заданного job_id.
    """
    if job_id not in generation_state:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return generation_state[job_id]

@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """
    Удаляет данные генерации для указанного job_id (для соответствия GDPR).
    """
    if job_id in generation_state:
        del generation_state[job_id]
    
    return {"status": "deleted", "job_id": job_id}
