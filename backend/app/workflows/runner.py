import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.models.workflow import Workflow, WorkflowRun
from app.workflows.engine import WorkflowAutomationEngine

logger = logging.getLogger(__name__)


class BackgroundTask:
    """Represents a single background task with lifecycle tracking."""

    def __init__(self, task_id: str, name: str, task_type: str, payload: Dict[str, Any],
                 scheduled_at: Optional[datetime] = None, retry_count: int = 0, max_retries: int = 3):
        self.id = task_id
        self.name = name
        self.task_type = task_type
        self.payload = payload
        self.status = "pending"
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.scheduled_at = scheduled_at or datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.duration_ms: Optional[int] = None
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "status": self.status,
            "payload": self.payload,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat(),
        }


class TaskQueue:
    """In-memory task queue with scheduling and retry support."""

    def __init__(self) -> None:
        self._tasks: Dict[str, BackgroundTask] = {}
        self._lock = asyncio.Lock()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("Task queue worker started")

    async def shutdown(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Task queue worker stopped")

    async def enqueue(self, task: BackgroundTask) -> str:
        async with self._lock:
            self._tasks[task.id] = task
        logger.info(f"Enqueued task {task.id} ({task.name}, type={task.task_type})")
        return task.id

    async def get(self, task_id: str) -> Optional[BackgroundTask]:
        async with self._lock:
            return self._tasks.get(task_id)

    async def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        async with self._lock:
            tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in tasks[:limit]]

    async def cancel(self, task_id: str) -> bool:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status in ("pending", "running"):
                task.status = "cancelled"
                task.completed_at = datetime.utcnow()
                return True
        return False

    async def retry(self, task_id: str) -> Optional[str]:
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status not in ("failed", "cancelled"):
                return None
            if task.retry_count >= task.max_retries:
                return None
            new_task = BackgroundTask(
                task_id=str(uuid4()),
                name=task.name,
                task_type=task.task_type,
                payload=task.payload,
                retry_count=task.retry_count + 1,
                max_retries=task.max_retries,
            )
            self._tasks[new_task.id] = new_task
            return new_task.id
        return None

    async def _worker_loop(self) -> None:
        while self._running:
            try:
                await self._process_next()
            except Exception as e:
                logger.error(f"Task worker error: {e}")
            await asyncio.sleep(0.5)

    async def _process_next(self) -> None:
        async with self._lock:
            pending = [t for t in self._tasks.values()
                       if t.status == "pending" and t.scheduled_at <= datetime.utcnow()]
            if not pending:
                return
            task = pending[0]
            task.status = "running"
            task.started_at = datetime.utcnow()

        start = time.monotonic()
        try:
            result = await self._execute_task(task)
            task.status = "completed"
            task.result = result
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            task.retry_count += 1
            if task.retry_count <= task.max_retries:
                task.status = "pending"
                task.error = str(e)
                task.scheduled_at = datetime.utcnow() + timedelta(seconds=2 ** task.retry_count)
                logger.info(f"Task {task.id} scheduled for retry {task.retry_count}/{task.max_retries}")
            else:
                task.status = "failed"
                task.error = str(e)
                logger.error(f"Task {task.id} failed after {task.max_retries} retries")
        finally:
            task.completed_at = datetime.utcnow()
            task.duration_ms = int((time.monotonic() - start) * 1000)

    async def _execute_task(self, task: BackgroundTask) -> Dict[str, Any]:
        dispatchers = {
            "workflow": self._dispatch_workflow,
            "webhook": self._dispatch_webhook,
            "cleanup": self._dispatch_cleanup,
        }
        dispatcher = dispatchers.get(task.task_type)
        if not dispatcher:
            raise ValueError(f"Unknown task type: {task.task_type}")
        return await dispatcher(task)

    async def _dispatch_workflow(self, task: BackgroundTask) -> Dict[str, Any]:
        payload = task.payload
        workflow_id = payload.get("workflow_id")
        if not workflow_id:
            raise ValueError("workflow_id required in payload")
        db: Session = SessionLocal()
        try:
            wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not wf:
                raise ValueError(f"Workflow {workflow_id} not found")
            results = await WorkflowAutomationEngine.trigger_event(
                event_name=wf.trigger_type,
                payload=payload.get("trigger_payload", {}),
                active_workflows=[{
                    "id": wf.id,
                    "name": wf.name,
                    "trigger_type": wf.trigger_type,
                    "condition_rules": wf.condition_rules or {},
                    "actions": wf.actions or [],
                }],
            )
            return {"workflow_id": workflow_id, "results": results}
        finally:
            db.close()

    async def _dispatch_webhook(self, task: BackgroundTask) -> Dict[str, Any]:
        import httpx
        payload = task.payload
        url = payload.get("url")
        method = payload.get("method", "POST")
        headers = payload.get("headers", {"Content-Type": "application/json"})
        body = payload.get("body", {})
        timeout = payload.get("timeout", 30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(method, url, json=body, headers=headers)
            resp.raise_for_status()
            return {"status_code": resp.status_code, "body": resp.text}

    async def _dispatch_cleanup(self, task: BackgroundTask) -> Dict[str, Any]:
        payload = task.payload
        task_type = payload.get("type", "runs")
        older_than_days = payload.get("older_than_days", 7)
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        db = SessionLocal()
        try:
            if task_type == "runs":
                deleted = db.query(WorkflowRun).filter(
                    WorkflowRun.completed_at < cutoff
                ).delete()
                db.commit()
                return {"deleted_runs": deleted}
            return {"type": task_type, "status": "ok"}
        finally:
            db.close()


class WorkflowRunner:
    """Persists workflow runs and executes actions in background."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.task_queue = TaskQueue()
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        try:
            self.scheduler.start()
            asyncio.get_running_loop().create_task(self.task_queue.start())
        except Exception:
            pass

    async def shutdown(self) -> None:
        if self._started:
            try:
                self.scheduler.shutdown(wait=False)
            except Exception:
                pass
            await self.task_queue.shutdown()
            self._started = False

    @staticmethod
    async def execute(workflow_id: str, trigger_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow and persist a WorkflowRun."""
        db: Session = SessionLocal()
        try:
            wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not wf:
                return {"status": "error", "error": f"workflow {workflow_id} not found"}

            run = WorkflowRun(
                id=str(uuid4()),
                workflow_id=workflow_id,
                status="running",
                trigger_payload=trigger_payload,
                started_at=datetime.utcnow(),
            )
            db.add(run)
            db.commit()
            db.refresh(run)

            try:
                results = await WorkflowAutomationEngine.trigger_event(
                    event_name=wf.trigger_type,
                    payload=trigger_payload,
                    active_workflows=[{
                        "id": wf.id,
                        "name": wf.name,
                        "trigger_type": wf.trigger_type,
                        "condition_rules": wf.condition_rules or {},
                        "actions": wf.actions or [],
                    }],
                )
                execution_result = results[0] if results else {"status": "no_match", "actions": []}
            except Exception as e:
                execution_result = {"status": "failed", "error": str(e)}

            run.status = "completed" if execution_result.get("status") == "completed" else "failed"
            run.execution_result = execution_result
            run.completed_at = datetime.utcnow()
            db.commit()
            return {"run_id": run.id, "status": run.status, "result": execution_result}
        finally:
            db.close()

    async def schedule_background(self, name: str, task_type: str, payload: Dict[str, Any],
                                  run_at: Optional[datetime] = None,
                                  max_retries: int = 3) -> str:
        """Enqueue a background task. Returns task ID immediately."""
        task = BackgroundTask(
            task_id=str(uuid4()),
            name=name,
            task_type=task_type,
            payload=payload,
            scheduled_at=run_at,
            max_retries=max_retries,
        )
        task_id = await self.task_queue.enqueue(task)
        return task_id

    def schedule_cron(self, workflow_id: str, cron_expr: str, name: str = "") -> str:
        """Schedule a workflow to run on a cron expression. Returns job ID."""
        job_id = f"cron:{workflow_id}:{uuid4()}"
        self.scheduler.add_job(
            self._run_cron_workflow,
            trigger=CronTrigger.from_crontab(cron_expr),
            args=[workflow_id],
            id=job_id,
            name=name or f"cron-{workflow_id}",
            replace_existing=True,
        )
        logger.info(f"Scheduled cron job {job_id} for workflow {workflow_id} with expression {cron_expr}")
        return job_id

    def remove_cron(self, job_id: str) -> bool:
        """Remove a scheduled cron job."""
        jobs = self.scheduler.get_jobs()
        if any(j.id == job_id for j in jobs):
            self.scheduler.remove_job(job_id)
            return True
        return False

    @staticmethod
    async def _run_cron_workflow(workflow_id: str) -> None:
        await WorkflowRunner.execute(workflow_id, {"_cron": True})

    def schedule_interval(self, workflow_id: str, seconds: int, name: str = "") -> str:
        """Schedule a workflow to run at a fixed interval. Returns job ID."""
        job_id = f"interval:{workflow_id}:{uuid4()}"
        self.scheduler.add_job(
            self._run_cron_workflow,
            trigger=IntervalTrigger(seconds=seconds),
            args=[workflow_id],
            id=job_id,
            name=name or f"interval-{workflow_id}",
            replace_existing=True,
        )
        logger.info(f"Scheduled interval job {job_id} for workflow {workflow_id} every {seconds}s")
        return job_id

    def remove_interval(self, job_id: str) -> bool:
        jobs = self.scheduler.get_jobs()
        if any(j.id == job_id for j in jobs):
            self.scheduler.remove_job(job_id)
            return True
        return False

    def list_scheduled_jobs(self) -> List[Dict[str, Any]]:
        jobs = self.scheduler.get_jobs()
        return [{"id": j.id, "name": j.name, "next_run": str(j.next_run_time)} for j in jobs]


def get_active_workflows_for_event(db: Session, event_name: str, workspace_id: Optional[str] = None) -> List[Workflow]:
    q = db.query(Workflow).filter(Workflow.trigger_type == event_name, Workflow.is_active.is_(True))
    if workspace_id:
        q = q.filter(Workflow.workspace_id == workspace_id)
    return q.all()


async def emit_event(event_name: str, payload: Dict[str, Any], workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Dispatch an event to all active workflows matching the trigger."""
    db = SessionLocal()
    try:
        workflows = get_active_workflows_for_event(db, event_name, workspace_id)
        results: List[Dict[str, Any]] = []
        for wf in workflows:
            r = await WorkflowRunner.execute(wf.id, payload)
            results.append(r)
        return results
    finally:
        db.close()


runner = WorkflowRunner()
