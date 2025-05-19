from temporalio import workflow, activity
import logging
import uuid

# Настройка логирования
logger = logging.getLogger(__name__)

@workflow.defn
class GenerateSiteWorkflow:
    @workflow.run
    async def run(self, job_id: str, format: str = "next"):
        try:
            logger.info(f"Starting workflow for job: {job_id}, format: {format}")
            
            # Шаг 1: Vision - сегментация и анализ UI изображения
            ui_json = await workflow.execute_activity(
                "vision.segment", 
                job_id, 
                start_to_close_timeout=workflow.timeout.from_seconds(300)
            )
            logger.info(f"Vision segmentation completed for job: {job_id}")
            
            # Шаг 2: CodeGen - генерация кода на основе UI JSON
            code_gen_params = {
                "ui_json": ui_json,
                "format": format,
                "job_id": job_id
            }
            code_result = await workflow.execute_activity(
                "codegen.generate", 
                code_gen_params, 
                start_to_close_timeout=workflow.timeout.from_seconds(600)
            )
            
            if not code_result.get("complete", False):
                return {"status": "FAILED", "reason": "CODE_GENERATION_FAILED: Unable to generate code"}
            
            logger.info(f"Code generation completed for job: {job_id}")
            
            # Шаг 3: Gen3D - генерация 3D моделей для UI элементов
            if "3d" in ui_json:
                gen3d_resp = await workflow.execute_activity(
                    "gen3d.generate", 
                    ui_json["3d"], 
                    start_to_close_timeout=workflow.timeout.from_seconds(600)
                )
                
                # Проверяем оба условия - fallback и отсутствие glb_url
                if gen3d_resp.get("fallback", False):
                    # Fallback? Прерываем и отдаём статус FAILED — фронт покажет понятное сообщение.
                    return {"status": "FAILED", "reason": gen3d_resp.get("error", "Unknown 3D generation error")}
                
                # Дополнительная проверка на отсутствие glb_url, даже если fallback не установлен
                if not gen3d_resp.get("glb_url"):
                    return {"status": "FAILED", "reason": "NO_MESH: 3D generation failed, no mesh URL provided."}
                
                logger.info(f"3D generation completed for job: {job_id}")
            
            # Шаг 4: QA - проверка качества сгенерированного кода и 3D моделей
            qa_result = await workflow.execute_activity(
                "qa.check", 
                job_id,
                start_to_close_timeout=workflow.timeout.from_seconds(300)
            )
            
            if not qa_result.get("passed", False):
                logger.warning(f"QA check failed for job: {job_id}")
                # Продолжаем выполнение, но добавляем предупреждение в результат
            
            # Шаг 5: Export - упаковка всех файлов в ZIP
            export_params = {"job_id": job_id}
            zip_result = await workflow.execute_activity(
                "export.bundle", 
                export_params,
                start_to_close_timeout=workflow.timeout.from_seconds(300)
            )
            
            logger.info(f"Workflow completed successfully for job: {job_id}")
            return {
                "status": "SUCCESS", 
                "download": zip_result.get("url"),
                "job_id": job_id,
                "warnings": qa_result.get("warnings", [])
            }
            
        except Exception as e:
            logger.error(f"Workflow failed for job: {job_id}, error: {str(e)}")
            return {"status": "FAILED", "reason": f"WORKFLOW_ERROR: {str(e)}", "job_id": job_id}
