from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

class IssueSeverity(Enum): BLOCKER='blocker'; HIGH='high'; MEDIUM='medium'; LOW='low'
class FixKind(Enum): QUARANTINE_MOD='quarantine_mod'; RENAME_CONFIG='rename_config'
@dataclass
class Fix:
    kind: FixKind; issue_id: str; description: str; payload: dict[str,Any]=field(default_factory=dict); reversible: bool=True
@dataclass
class Issue:
    id: str; severity: IssueSeverity; category: str; title: str; detail: str=''; related_files: list[Path]=field(default_factory=list); suggested_fix: Fix|None=None; evidence: dict[str,Any]=field(default_factory=dict)
@dataclass
class RepairResult:
    applied: bool; rollback_data: dict[str,Any]=field(default_factory=dict); error: str|None=None
