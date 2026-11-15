"""
CHAMP Phase 10 — memory/task_memory.py

Task Memory & Checkpoint Persistence Manager.

Tracks multi-step task execution, step statuses, file metadata, web/RAG results, and persists checkpoints to disk for crash recovery.
"""

from __future__ import annotations
import time
import uuid
from typing import TypedDict, Any
from pathlib import Path
from memory.memory_store import MemoryStore
from utils.logger import get_logger

log = get_logger("muthuai.memory.task_memory")


class TaskStepData(TypedDict):
    step_id: int
    tool: str
    arguments: dict[str, Any]
    status: str  # PENDING | RUNNING | VERIFIED | FAILED | CANCELLED
    verification: str
    checkpoint_data: dict[str, Any]


class TaskMemoryData(TypedDict):
    task_id: str
    task_name: str
    task_state: str  # PENDING | RUNNING | PAUSED | CANCELLED | COMPLETED | FAILED
    steps: list[TaskStepData]
    completed_steps: list[int]
    failed_steps: list[int]
    current_step: int
    created_files: list[dict[str, Any]]
    opened_apps: list[str]
    web_results: list[dict[str, Any]]
    rag_results: list[dict[str, Any]]
    summaries: list[str]


class TaskMemoryManager:
    """
    Manages active task state, checkpoints, and crash recovery.
    """

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()
        saved = self.store.load("active_task", default={})
        self.active_task: TaskMemoryData = {
            "task_id": saved.get("task_id", ""),
            "task_name": saved.get("task_name", ""),
            "task_state": saved.get("task_state", "IDLE"),
            "steps": saved.get("steps", []),
            "completed_steps": saved.get("completed_steps", []),
            "failed_steps": saved.get("failed_steps", []),
            "current_step": saved.get("current_step", 0),
            "created_files": saved.get("created_files", []),
            "opened_apps": saved.get("opened_apps", []),
            "web_results": saved.get("web_results", []),
            "rag_results": saved.get("rag_results", []),
            "summaries": saved.get("summaries", []),
        }

    def _save_checkpoint(self) -> None:
        """Persist task state checkpoint to disk."""
        if self.active_task["task_id"]:
            self.store.save("active_task", self.active_task)
            self.store.save("task_checkpoints", self.active_task)
            log.debug("Saved task checkpoint for '%s' (Step %d/%d)",
                      self.active_task["task_name"],
                      self.active_task["current_step"],
                      len(self.active_task["steps"]))

    def create_task(self, name: str, steps: list[dict[str, Any]]) -> str:
        """Initialize a new multi-step task with checkpointing."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        formatted_steps: list[TaskStepData] = []
        for idx, s in enumerate(steps, start=1):
            formatted_steps.append({
                "step_id": idx,
                "tool": s.get("tool", ""),
                "arguments": s.get("arguments", {}),
                "status": "PENDING",
                "verification": "",
                "checkpoint_data": {},
            })

        self.active_task = {
            "task_id": task_id,
            "task_name": name,
            "task_state": "RUNNING",
            "steps": formatted_steps,
            "completed_steps": [],
            "failed_steps": [],
            "current_step": 1,
            "created_files": [],
            "opened_apps": [],
            "web_results": [],
            "rag_results": [],
            "summaries": [],
        }
        log.info("Created Task '%s' (ID: %s) with %d steps.", name, task_id, len(steps))
        self._save_checkpoint()
        return task_id

    def update_step_status(self, step_id: int, status: str, verification: str = "", checkpoint: dict | None = None) -> None:
        """Update step status (VERIFIED | FAILED) and persist checkpoint."""
        for step in self.active_task["steps"]:
            if step["step_id"] == step_id:
                step["status"] = status
                step["verification"] = verification
                if checkpoint:
                    step["checkpoint_data"] = checkpoint

                if status == "VERIFIED" and step_id not in self.active_task["completed_steps"]:
                    self.active_task["completed_steps"].append(step_id)
                elif status == "FAILED" and step_id not in self.active_task["failed_steps"]:
                    self.active_task["failed_steps"].append(step_id)

                self.active_task["current_step"] = step_id + 1
                if len(self.active_task["completed_steps"]) == len(self.active_task["steps"]):
                    self.active_task["task_state"] = "COMPLETED"

                self._save_checkpoint()
                return

    def record_created_file(self, file_path: str | Path, app: str = "", purpose: str = "") -> None:
        """Record file creation metadata in task memory."""
        p = Path(file_path)
        meta = {
            "path": str(p),
            "name": p.name,
            "size": p.stat().st_size if p.exists() else 0,
            "created_at": time.time(),
            "app": app,
            "task_id": self.active_task["task_id"],
            "purpose": purpose,
        }
        self.active_task["created_files"].append(meta)
        log.info("TaskMemory: Recorded created file %r (%d bytes)", p.name, meta["size"])
        self._save_checkpoint()

    def cancel_task(self) -> None:
        """Cancel active task state."""
        self.active_task["task_state"] = "CANCELLED"
        self._save_checkpoint()
        log.info("TaskMemory: Task '%s' marked CANCELLED.", self.active_task["task_name"])

    def get_last_incomplete_step(self) -> TaskStepData | None:
        """Find last incomplete step for resumption."""
        for step in self.active_task["steps"]:
            if step["status"] not in ("VERIFIED", "COMPLETED"):
                return step
        return None

    def resume_task(self) -> dict[str, Any]:
        """Resume task execution from last verified checkpoint."""
        step = self.get_last_incomplete_step()
        if not step:
            return {"status": "no_resume_needed", "message": "All steps already completed."}

        self.active_task["task_state"] = "RUNNING"
        self._save_checkpoint()
        log.info("TaskMemory: Resuming task '%s' from Step %d (%s)",
                 self.active_task["task_name"], step["step_id"], step["tool"])
        return {"status": "resuming", "step": step, "task_id": self.active_task["task_id"]}

    def clear_task(self) -> None:
        """Clear active task memory."""
        self.active_task = {
            "task_id": "",
            "task_name": "",
            "task_state": "IDLE",
            "steps": [],
            "completed_steps": [],
            "failed_steps": [],
            "current_step": 0,
            "created_files": [],
            "opened_apps": [],
            "web_results": [],
            "rag_results": [],
            "summaries": [],
        }
        self.store.delete("active_task")
        log.info("TaskMemory reset.")
