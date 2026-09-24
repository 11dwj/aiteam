#!/usr/bin/env python3
"""Dependency-free quality/evidence gate for the team trial package.

This gate checks whether a change has recorded the high-risk engineering
dimensions.  It does not claim that the business behavior is correct; that
still requires a real entry point and business assertions.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Dict, List, Optional, Tuple


REQUIRED_DIMENSIONS = (
    "public_rule_reuse",
    "n_plus_one",
    "pagination_count_export",
    "transaction_rollback",
    "state_idempotency",
    "permission_scope",
    "sql_null_type",
    "observability_cleanup",
)
DIMENSION_RULES = {
    "public_rule_reuse": (".java", ".groovy", ".kt", ".ts", ".tsx", ".js", ".jsx"),
    "n_plus_one": ("query", "select", "find", "dao", "mapper", "repository"),
    "pagination_count_export": ("page", "分页", "count", "export", "导出"),
    "transaction_rollback": ("transaction", "事务", "rollback", "回滚", "create", "store", "update", "delete"),
    "state_idempotency": ("status", "state", "approve", "reject", "recall", "驳回", "撤回", "幂等"),
    "permission_scope": ("permission", "role", "auth", "组织", "权限", "scope"),
    "sql_null_type": ("sql", "query", "select", "null", "schema", "mapper", "dao"),
    "observability_cleanup": ("log", "logger", "trace", "cleanup", "清理", "残留"),
}
VALID_STATUSES = {"NOT_APPLICABLE", "NOT_CHECKED", "PASS", "FAIL", "TEST_BLOCKED", "NEEDS_REVIEW"}
QUERY_IN_LOOP = re.compile(r"(?:for\s*\([^)]*\)|while\s*\([^)]*\)|\.forEach\s*\([^)]*\))\s*\{[^}]{0,600}?(?:\.find\w*\s*\(|\.query(?:List|One)?\s*\(|\bselect\s+)", re.IGNORECASE | re.DOTALL)
PUBLIC_DECL = re.compile(r"\bpublic\s+(?:abstract\s+|final\s+|static\s+)*(?:class|interface|enum)\s+([A-Za-z_]\w*)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Harness engineering quality and evidence gate")
    parser.add_argument("--project", required=True)
    parser.add_argument("--ticket")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--evidence-file", help="project-relative JSON evidence file")
    parser.add_argument("--write-template", action="store_true")
    return parser.parse_args()


def rel_path(project: Path, value: str) -> Path:
    """Resolve a project-relative path without traversal or symlink escape."""
    candidate = Path(value)
    if Path(value).is_absolute() or PureWindowsPath(value).is_absolute() or value.startswith(("/", "\\")) or ".." in candidate.parts:
        raise ValueError("EVIDENCE_PATH_OUTSIDE_PROJECT")
    root = project.resolve()
    resolved = (root / candidate).resolve(strict=False)
    if resolved != root and root not in resolved.parents:
        raise ValueError("EVIDENCE_PATH_OUTSIDE_PROJECT")
    return resolved


def active_dimensions(changed_files: list[str]) -> list[str]:
    if not changed_files:
        return list(REQUIRED_DIMENSIONS)
    lowered = [value.replace("\\", "/").lower() for value in changed_files]
    result = []
    for dimension in REQUIRED_DIMENSIONS:
        markers = DIMENSION_RULES[dimension]
        if dimension == "public_rule_reuse":
            matched = any(path.endswith(markers) for path in lowered)
        else:
            matched = any(marker in path for path in lowered for marker in markers)
        if matched:
            result.append(dimension)
    if not result:
        result.append("public_rule_reuse")
    return result


def template(ticket: Optional[str], changed_files: List[str]) -> Dict[str, object]:
    active = set(active_dimensions(changed_files))
    return {
        "ticket": ticket or "TICKET-ID",
        "scope": "changed files and affected entry points",
        "dimensions": {
            key: {
                "status": "NOT_CHECKED" if key in active else "NOT_APPLICABLE",
                "evidence": [],
                "finding": "",
                "next_action": "",
            }
            for key in REQUIRED_DIMENSIONS
        },
        "verification": {
            "verification_kind": "STATIC_REVIEW",
            "command": "",
            "entry": "",
            "business_assertions": [],
            "technical_status": "NOT_RUN",
            "business_status": "NOT_RUN",
        },
        "human_decision": "PENDING_CONFIRMATION",
        "generated_by": "harness quality-gate",
    }


def load_evidence(path: Path) -> Tuple[Optional[Dict[str, object]], List[str]]:
    if not path.is_file():
        return None, [f"EVIDENCE_FILE_MISSING={path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"EVIDENCE_FILE_INVALID={exc}"]
    if not isinstance(value, dict):
        return None, ["EVIDENCE_ROOT_MUST_BE_OBJECT"]
    return value, []


def inspect_changed_files(project: Path, values: list[str]) -> tuple[list[dict], list[str]]:
    findings: list[dict] = []
    errors: list[str] = []
    for raw in values:
        try:
            path = rel_path(project, raw)
        except ValueError:
            errors.append(f"CHANGED_FILE_OUTSIDE_PROJECT={raw}")
            continue
        if not path.is_file():
            errors.append(f"CHANGED_FILE_MISSING={raw}")
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"CHANGED_FILE_UNREADABLE={raw}:{exc}")
            continue
        query_match = QUERY_IN_LOOP.search(text)
        if query_match:
            line = text.count("\n", 0, query_match.start()) + 1
            findings.append({"rule": "N_PLUS_ONE_REVIEW", "file": raw, "line": line, "severity": "REVIEW", "message": "query-like call appears inside a loop; record query-count evidence or explain why it is safe"})
        public_names = PUBLIC_DECL.findall(text)
        if len(public_names) > 1 and path.suffix.lower() in {".java", ".groovy", ".kt"}:
            findings.append({"rule": "PUBLIC_RULE_REUSE", "file": raw, "severity": "REVIEW", "message": "multiple public declarations found; record reuse/search result and ownership of shared rules"})
    return findings, errors


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(json.dumps({"execution_status": "BLOCKED", "blocker_code": "PROJECT_NOT_FOUND"}, ensure_ascii=False, indent=2))
        return 2
    try:
        evidence_path = rel_path(project, args.evidence_file) if args.evidence_file else None
    except ValueError as exc:
        print(json.dumps({"execution_status": "BLOCKED", "blocker_code": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    if args.write_template:
        target = evidence_path or project / "harness" / "evidence" / (args.ticket or "quality-review") / "quality-evidence.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(json.dumps(template(args.ticket, args.changed_file), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        evidence_path = target
    evidence, errors = load_evidence(evidence_path) if evidence_path else (None, ["EVIDENCE_FILE_REQUIRED"])
    findings, file_errors = inspect_changed_files(project, args.changed_file)
    errors.extend(file_errors)
    dimension_errors: list[str] = []
    dimensions = evidence.get("dimensions", {}) if evidence else {}
    if not isinstance(dimensions, dict):
        dimension_errors.append("DIMENSIONS_MUST_BE_OBJECT")
        dimensions = {}
    required_dimensions = active_dimensions(args.changed_file)
    for key in required_dimensions:
        item = dimensions.get(key)
        if not isinstance(item, dict):
            dimension_errors.append(f"DIMENSION_MISSING={key}")
            continue
        status = item.get("status")
        if status not in VALID_STATUSES:
            dimension_errors.append(f"DIMENSION_STATUS_INVALID={key}")
        elif status == "NOT_CHECKED":
            dimension_errors.append(f"DIMENSION_NOT_CHECKED={key}")
        if status in {"PASS", "FAIL", "NEEDS_REVIEW", "TEST_BLOCKED"} and not item.get("evidence") and not item.get("finding"):
            dimension_errors.append(f"DIMENSION_EVIDENCE_MISSING={key}")
    errors.extend(dimension_errors)
    technical_status = "PASS" if not errors and not any(item.get("severity") == "BLOCK" for item in findings) else "FAIL"
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ticket": args.ticket,
        "execution_status": technical_status,
        "technical_status": technical_status,
        "business_status": "NOT_RUN",
        "business_pass_allowed": False,
        "business_pass_reason": "quality-gate checks evidence completeness and review signals only; run a real entry point with business assertions separately",
        "evidence_file": str(evidence_path.relative_to(project)).replace("\\", "/") if evidence_path and evidence_path.is_relative_to(project) else None,
        "changed_files": args.changed_file,
        "findings": findings,
        "blockers": errors,
        "dimensions": required_dimensions,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if technical_status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
