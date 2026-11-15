"""
CHAMP — n8n Workflow Scanner.
Phase 11.0: Discovery & Capability Audit.

Scans project directories and custom input paths to locate all n8n workflow JSON
files, exports, collections, and webhook definitions without executing any workflow.
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from utils.logger import get_logger
from .parser import ParsedWorkflow, WorkflowParser

log = get_logger("muthuai.n8n.scanner")

# Default potential workflow search directories relative to project root
DEFAULT_SEARCH_DIRS = [
    "data/n8n_workflows",
    "n8n/workflows",
    "workflows",
    "data/workflows",
    "config/workflows",
]


@dataclass
class ScanResult:
    """Result of a workflow directory discovery scan."""
    source_status: str  # "FOUND" or "NOT_FOUND"
    scanned_paths: List[str]
    discovered_files: List[str]
    workflows: List[ParsedWorkflow]
    total_workflows: int
    parsing_failures: int
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_status": self.source_status,
            "scanned_paths": self.scanned_paths,
            "discovered_files": self.discovered_files,
            "total_workflows": self.total_workflows,
            "parsing_failures": self.parsing_failures,
            "summary": self.summary,
            "workflows": [wf.to_dict() for wf in self.workflows],
        }


class WorkflowScanner:
    """Scanner for discovering and loading n8n workflow files."""

    def __init__(self, parser: Optional[WorkflowParser] = None) -> None:
        self.parser = parser or WorkflowParser()

    def scan(
        self,
        search_paths: Optional[Sequence[Union[str, Path]]] = None,
        project_root: Optional[Union[str, Path]] = None,
    ) -> ScanResult:
        """
        Scan configured search paths for n8n workflow JSON files.
        Never executes any workflow.
        """
        root = Path(project_root) if project_root else Path.cwd()
        
        # Build list of directories to inspect
        target_dirs: List[Path] = []
        if search_paths:
            for p in search_paths:
                path_obj = Path(p)
                if not path_obj.is_absolute():
                    path_obj = root / path_obj
                target_dirs.append(path_obj)
        else:
            # Check environment variable first if provided
            env_path = os.environ.get("N8N_WORKFLOW_DIR")
            if env_path:
                target_dirs.append(Path(env_path))
            for rel in DEFAULT_SEARCH_DIRS:
                target_dirs.append(root / rel)

        scanned_paths_str = [str(p) for p in target_dirs]
        discovered_files: List[Path] = []

        for directory in target_dirs:
            if not directory.exists() or not directory.is_dir():
                continue

            # Discover all json files recursively
            for file_path in directory.rglob("*.json"):
                if self._is_candidate_workflow_file(file_path):
                    discovered_files.append(file_path)

        # If no files found in designated workflow dirs, check for any .json files in root/data
        if not discovered_files and not search_paths:
            # Check root or data folder without assuming fixed names
            candidate_dirs = [root / "data", root / "n8n"]
            for c_dir in candidate_dirs:
                if c_dir.exists():
                    for file_path in c_dir.glob("*.json"):
                        if self._is_candidate_workflow_file(file_path):
                            discovered_files.append(file_path)

        all_workflows: List[ParsedWorkflow] = []
        parsing_failures = 0

        for file_path in discovered_files:
            parsed_list = self.parser.parse_file(file_path)
            for wf in parsed_list:
                if wf.parse_error:
                    parsing_failures += 1
                all_workflows.append(wf)

        source_status = "FOUND" if (discovered_files and all_workflows) else "NOT_FOUND"

        result = ScanResult(
            source_status=source_status,
            scanned_paths=scanned_paths_str,
            discovered_files=[str(p) for p in discovered_files],
            workflows=all_workflows,
            total_workflows=len(all_workflows),
            parsing_failures=parsing_failures,
            summary={
                "N8N_WORKFLOW_SOURCE": source_status if source_status == "FOUND" else "NOT_FOUND",
                "total_files": len(discovered_files),
                "total_workflows": len(all_workflows),
            }
        )

        log.info(
            "WorkflowScanner finished: source_status=%s, files=%d, workflows=%d, failures=%d",
            source_status,
            len(discovered_files),
            len(all_workflows),
            parsing_failures,
        )
        return result

    def _is_candidate_workflow_file(self, file_path: Path) -> bool:
        """Quickly check if a JSON file matches n8n workflow markers."""
        try:
            # Avoid scanning huge non-workflow database/log files
            if file_path.stat().st_size > 5 * 1024 * 1024:
                return False
            
            # Read first chunk of file to detect n8n markers
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                header = f.read(2048)
                # Standard n8n markers
                markers = ["nodes", "connections", "workflow", "n8n-nodes-base", "trigger"]
                if any(m in header for m in markers):
                    return True
        except Exception:
            pass
        return False


def scan_workflows(
    search_paths: Optional[Sequence[Union[str, Path]]] = None,
    project_root: Optional[Union[str, Path]] = None,
) -> ScanResult:
    """Convenience helper to run a workflow scan."""
    return WorkflowScanner().scan(search_paths=search_paths, project_root=project_root)
