from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.workflows.runner import runner
from app.schemas.api_schemas import EnqueueTaskRequest, ScheduleCronRequest, ScheduleIntervalRequest

router = APIRouter(prefix="/background-tasks", tags=["Background Tasks"])


@router.post("/enqueue")
async def enqueue_task(req: EnqueueTaskRequest, db: Session = Depends(get_db)):
    """Enqueue a background task for async execution."""
    if req.task_type not in ("workflow", "webhook", "cleanup"):
        raise HTTPException(status_code=400, detail="task_type must be one of: workflow, webhook, cleanup")

    task_id = await runner.schedule_background(
        name=req.name,
        task_type=req.task_type,
        payload=req.payload,
        run_at=req.run_at,
        max_retries=req.max_retries,
    )
    return {"task_id": task_id, "status": "enqueued"}


@router.get("/tasks")
async def list_tasks(status: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    """List background tasks with optional status filter."""
    tasks = await runner.task_queue.list_tasks(status=status, limit=limit)
    return tasks


@router.get("/tasks/{task_id}")
async def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific background task by ID."""
    task = await runner.task_queue.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task.to_dict()


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, db: Session = Depends(get_db)):
    """Cancel a pending or running task."""
    success = await runner.task_queue.cancel(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled (already completed or not found)")
    return {"task_id": task_id, "status": "cancelled"}


@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str, db: Session = Depends(get_db)):
    """Retry a failed or cancelled task."""
    new_id = await runner.task_queue.retry(task_id)
    if not new_id:
        raise HTTPException(status_code=400, detail="Task cannot be retried (max retries exceeded or wrong status)")
    return {"task_id": task_id, "new_task_id": new_id, "status": "retry_enqueued"}


@router.post("/schedule/cron")
async def schedule_cron(req: ScheduleCronRequest, db: Session = Depends(get_db)):
    """Schedule a workflow to run on a cron expression."""
    job_id = runner.schedule_cron(workflow_id=req.workflow_id, cron_expr=req.cron_expr, name=req.name)
    return {"job_id": job_id, "workflow_id": req.workflow_id, "cron": req.cron_expr}


@router.delete("/schedule/cron/{job_id}")
async def remove_cron(job_id: str, db: Session = Depends(get_db)):
    """Remove a scheduled cron job."""
    success = runner.remove_cron(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Cron job {job_id} not found")
    return {"job_id": job_id, "status": "removed"}


@router.post("/schedule/interval")
async def schedule_interval(req: ScheduleIntervalRequest, db: Session = Depends(get_db)):
    """Schedule a workflow to run at a fixed interval."""
    if req.seconds < 10:
        raise HTTPException(status_code=400, detail="Interval must be at least 10 seconds")
    job_id = runner.schedule_interval(workflow_id=req.workflow_id, seconds=req.seconds, name=req.name)
    return {"job_id": job_id, "workflow_id": req.workflow_id, "interval_seconds": req.seconds}


@router.delete("/schedule/interval/{job_id}")
async def remove_interval(job_id: str, db: Session = Depends(get_db)):
    """Remove a scheduled interval job."""
    success = runner.remove_interval(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Interval job {job_id} not found")
    return {"job_id": job_id, "status": "removed"}


@router.get("/schedule/jobs")
async def list_jobs(db: Session = Depends(get_db)):
    """List all scheduled jobs (cron + interval)."""
    jobs = runner.list_scheduled_jobs()
    return jobs
