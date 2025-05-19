from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends, Header
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import uuid4
from pathlib import Path
import os
import mimetypes
import asyncio
import httpx
import logging
import json
import shutil
import time
from datetime import datetime, timedelta

# Импорт для Temporal Client
from temporalio.client import Client as TemporalClient
from temporalio.common import RetryPolicy
from temporalio.service import RPCError

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы
MAX_FILE_SIZE = 4 * 1024 * 1024  # 4 МБ
RATE_LIMIT_FREE = 60  # 60 запросов в час
RATE_LIMIT_PRO = 600  # 600 запросов в час
STORAGE_DIR = os.getenv("STORAGE_DIR", "/tmp/pix2fullcode")
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
WORKFLOW_TASK_QUEUE = os.getenv("WORKFLOW_TASK_QUEUE", "pix2fullcode-tasks")

# Модели данных
class UploadResponse(BaseModel):
    job_id: str
    status: str = "PENDING"
    message: str = "Image uploaded successfully"

class StatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    logs: List[str] = []
    eta: Optional[int] = None
    error: Optional[str] = None

class JobMetadata(BaseModel):
    job_id: str
    user_id: Optional[str] = None
    filename: str
    format: str = "next"
    timestamp: str
    status: str = "PENDING"
    progress: int = 0
    logs: List[str] = []

# Временное хранилище состояния задания (в реальном приложении использовался бы Redis или БД)
job_store = {}

app = FastAPI(title="Pix2FC Gateway")

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В производственной среде нужно указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создание Temporal клиента
temporal_client = None

@app.on_event("startup")
async def startup_event():
    global temporal_client
    try:
        # Подключение к Temporal серверу
        temporal_client = await TemporalClient.connect(TEMPORAL_HOST)
        logger.info(f"Connected to Temporal server at {TEMPORAL_HOST}")
    except Exception as e:
        logger.error(f"Failed to connect to Temporal server: {str(e)}")
        # Продолжаем работу в режиме симуляции
        temporal_client = None

# Защита от превышения лимита запросов
async def check_rate_limit(authorization: Optional[str] = Header(None)):
    user_id = "anonymous"
    tier = "free"
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        # Здесь должна быть валидация JWT и получение user_id и tier
        # Заглушка для демонстрации
        user_id = "demo_user"
        tier = "free"
    
    # Проверка лимита запросов (заглушка, в реальном приложении использовался бы Redis)
    limit = RATE_LIMIT_PRO if tier == "pro" else RATE_LIMIT_FREE
    current_requests = 1  # Заглушка - в реальном приложении счетчик из Redis
    
    if current_requests > limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return {"user_id": user_id, "tier": tier}

# Вспомогательные функции
def ensure_storage_dir(job_id: str) -> Path:
    """Создает и возвращает директорию для хранения файлов задания"""
    job_dir = Path(STORAGE_DIR) / f"job-{job_id}"
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir

async def start_workflow(job_id: str, format: str):
    """Запускает Temporal workflow для обработки загруженного изображения"""
    try:
        if temporal_client:
            # Запуск workflow через Temporal
            await temporal_client.start_workflow(
                "GenerateSiteWorkflow", 
                args=[job_id, format],
                id=f"pix2fullcode-{job_id}",
                task_queue=WORKFLOW_TASK_QUEUE,
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    maximum_interval_seconds=60
                )
            )
            logger.info(f"Started workflow for job {job_id}")
        else:
            # Симуляция workflow для демонстрации
            logger.info(f"Simulating workflow for job {job_id}")
            job_store[job_id]["status"] = "PROCESSING"
            job_store[job_id]["logs"].append(f"Started processing at {datetime.now().isoformat()}")
            
            # Запускаем бэкграунд-задачу для симуляции прогресса
            asyncio.create_task(simulate_progress(job_id))
            
    except Exception as e:
        logger.error(f"Failed to start workflow for job {job_id}: {str(e)}")
        job_store[job_id]["status"] = "FAILED"
        job_store[job_id]["error"] = str(e)

async def simulate_progress(job_id: str):
    """Симулирует прогресс обработки для демонстрации"""
    for progress in range(0, 101, 10):
        await asyncio.sleep(3)  # Симулируем задержку в обработке
        
        if job_id not in job_store:
            return
            
        job_store[job_id]["progress"] = progress
        job_store[job_id]["logs"].append(f"Progress: {progress}%")
        
        # Симулируем различные этапы
        if progress == 30:
            job_store[job_id]["logs"].append("Completed vision segmentation")
        elif progress == 50:
            job_store[job_id]["logs"].append("Generated code with DeepSeek")
        elif progress == 70:
            job_store[job_id]["logs"].append("Created 3D models")
        elif progress == 90:
            job_store[job_id]["logs"].append("Running quality checks")
        elif progress == 100:
            job_store[job_id]["status"] = "COMPLETED"
            job_store[job_id]["logs"].append("Processing completed successfully")
            
            # Создаем симуляцию ZIP-файла
            job_dir = ensure_storage_dir(job_id)
            with open(job_dir / "result.txt", "w") as f:
                f.write("This is a simulated result file")

# API эндпоинты
@app.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...), 
    format: str = "next",
    rate_limit: Dict = Depends(check_rate_limit),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # Проверка типа файла
    if file.content_type not in ("image/png", "image/jpeg"):
        raise HTTPException(status_code=400, detail="Only PNG/JPEG allowed")
    
    # Создаем уникальный идентификатор задания
    job_id = str(uuid4())
    
    # Сохраняем метаданные задания
    job_store[job_id] = {
        "job_id": job_id,
        "user_id": rate_limit["user_id"],
        "filename": file.filename,
        "format": format,
        "timestamp": datetime.now().isoformat(),
        "status": "PENDING",
        "progress": 0,
        "logs": ["Job created"],
    }
    
    # Сохраняем файл
    job_dir = ensure_storage_dir(job_id)
    file_extension = os.path.splitext(file.filename)[1]
    file_path = job_dir / f"upload{file_extension}"
    
    try:
        # Чтение и проверка размера файла
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_FILE_SIZE/1024/1024} MB")
        
        # Запись файла на диск
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Запуск обработки в фоновом режиме
        background_tasks.add_task(start_workflow, job_id, format)
        
        return UploadResponse(
            job_id=job_id,
            status="PENDING",
            message="Image uploaded successfully, processing started"
        )
    except Exception as e:
        logger.error(f"Error processing upload for job {job_id}: {str(e)}")
        # Очистка в случае ошибки
        if job_id in job_store:
            job_store[job_id]["status"] = "FAILED"
            job_store[job_id]["error"] = str(e)
        
        if temporal_client:
            # TODO: отмена workflow в случае ошибки
            pass
            
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/status/{job_id}", response_model=StatusResponse)
async def status(job_id: str):
    """Возвращает текущий статус обработки задания"""
    # Проверка наличия задания
    if job_id not in job_store:
        # Проверка Temporal (если доступен)
        if temporal_client:
            try:
                # Получаем статус из Temporal
                handle = temporal_client.get_workflow_handle(f"pix2fullcode-{job_id}")
                desc = await handle.describe()
                
                # Возвращаем статус на основе описания workflow
                status_map = {
                    "RUNNING": "PROCESSING",
                    "COMPLETED": "COMPLETED",
                    "FAILED": "FAILED",
                    "CANCELED": "CANCELED",
                    "TERMINATED": "TERMINATED",
                    "CONTINUED_AS_NEW": "PROCESSING",
                    "TIMED_OUT": "FAILED"
                }
                
                status = status_map.get(desc.status.name, "UNKNOWN")
                
                # Получаем результат, если workflow завершен
                result = None
                if status == "COMPLETED":
                    try:
                        result = await handle.result()
                    except Exception as e:
                        logger.error(f"Error getting workflow result for {job_id}: {str(e)}")
                
                return StatusResponse(
                    job_id=job_id,
                    status=status,
                    progress=100 if status == "COMPLETED" else 0,
                    logs=[f"Workflow status: {status}"],
                    error=str(desc.failure) if desc.failure else None
                )
            except RPCError:
                raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        else:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Возвращаем статус из локального хранилища
    job_data = job_store[job_id]
    
    # Расчет приблизительного ETA (если задание в процессе)
    eta = None
    if job_data["status"] == "PROCESSING" and job_data["progress"] > 0:
        # Простая линейная аппроксимация
        timestamp = datetime.fromisoformat(job_data["timestamp"])
        elapsed_seconds = (datetime.now() - timestamp).total_seconds()
        progress_per_second = job_data["progress"] / elapsed_seconds if elapsed_seconds > 0 else 0
        
        if progress_per_second > 0:
            remaining_seconds = (100 - job_data["progress"]) / progress_per_second
            eta = int(remaining_seconds)
    
    return StatusResponse(
        job_id=job_id,
        status=job_data["status"],
        progress=job_data["progress"],
        logs=job_data["logs"][-10:],  # Возвращаем только последние 10 записей лога
        eta=eta,
        error=job_data.get("error")
    )

@app.get("/download/{job_id}")
async def download(job_id: str):
    """Скачивание ZIP-архива с результатом обработки"""
    # Проверка наличия задания
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job_data = job_store[job_id]
    
    # Проверка статуса задания
    if job_data["status"] != "COMPLETED":
        raise HTTPException(
            status_code=400, 
            detail=f"Job is not completed yet. Current status: {job_data['status']}"
        )
    
    # Путь к файлу результата
    job_dir = ensure_storage_dir(job_id)
    result_file = job_dir / "result.txt"  # В реальном приложении здесь был бы ZIP
    
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Result file not found")
    
    return FileResponse(
        result_file,
        filename=f"pix2fullcode-{job_id}.txt",  # В реальном приложении здесь был бы ZIP
        media_type="text/plain"  # В реальном приложении здесь был бы application/zip
    )

@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Удаление задания и всех связанных с ним данных (GDPR)"""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Удаление данных из локального хранилища
    del job_store[job_id]
    
    # Удаление файлов
    job_dir = Path(STORAGE_DIR) / f"job-{job_id}"
    if job_dir.exists():
        shutil.rmtree(job_dir)
    
    # Остановка workflow в Temporal (если он запущен)
    if temporal_client:
        try:
            handle = temporal_client.get_workflow_handle(f"pix2fullcode-{job_id}")
            await handle.terminate("Deleted due to GDPR request")
        except Exception as e:
            logger.warning(f"Could not terminate workflow for job {job_id}: {str(e)}")
    
    return {"status": "deleted", "job_id": job_id}

@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {
        "status": "ok",
        "temporal_connected": temporal_client is not None,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }
