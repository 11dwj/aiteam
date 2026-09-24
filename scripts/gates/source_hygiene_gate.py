#!/usr/bin/env python3
"""Conservative changed-file source hygiene scanner and bounded cleaner."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

TEXT_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".kt", ".go", ".rs", ".rb",
    ".php", ".sh", ".ps1", ".sql", ".xml", ".yaml", ".yml", ".json", ".txt", ".md",
}
FORMAL_SEGMENTS = {"test", "tests", "fixture", "fixtures", "docs", "documentation"}
SAFE_TEMP_SUFFIXES = {".tmp", ".bak", ".orig", ".rej"}
TEMP_NAME_RE = re.compile(r"(?i)^(?:tmp|temp|scratch|debug|one[_-]?off|manual[_-]?test)[_.-]")
PATTERNS = (
    ("PYTHON_BREAKPOINT", re.compile(r"(?m)^\s*(?:breakpoint\(\)|pdb\.set_trace\(\)|import\s+pdb\s*;\s*pdb\.set_trace\(\))")),
    ("JAVASCRIPT_DEBUGGER", re.compile(r"(?m)^\s*debugger\s*;")),
    ("DEBUG_PRINT", re.compile(r"(?mi)^\s*(?:print|console\.log|System\.out\.println)\s*\(\s*[\"'](?:DEBUG|TEMP|REMOVE BEFORE COMMIT)")),
    ("TEMPORARY_MARKER", re.compile(r"(?i)HARNESS_TEMPORARY|TEMPORARY VALIDATION ONLY|REMOVE BEFORE COMMIT")),
    ("TEMPORARY_FAKE_DATA", re.compile(r"(?i)\b(?:DUMMY_DATA|FAKE_DATA|TEMP_API|TEMP_MOCK|HARDCODED_TEST_DATA)\b")),
)


def _inside(project: Path, raw: str) -> Path | None:
    candidate = Path(raw)
    if not raw or candidate.is_absolute() or ".." in candidate.parts:
        return None
    root = project.resolve()
    resolved = (root / candidate).resolve(strict=False)
    return resolved if resolved == root or root in resolved.parents else None


def _decode_nul(raw: bytes) -> List[str]:
    return [item.decode("utf-8", errors="surrogateescape") for item in raw.split(b"\0") if item]


def _git(project: Path, *args: str) -> subprocess.CompletedProcess[bytes] | None:
    try:
        return subprocess.run(
            ["git", "-C", str(project), *args],
            capture_output=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _parse_name_status(raw: bytes) -> List[Tuple[str, str]]:
    tokens = _decode_nul(raw)
    result: List[Tuple[str, str]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        if index >= len(tokens):
            break
        if status.startswith(("R", "C")):
            # name-status -z emits: Rnnn, old path, new path
            index += 1  # skip source path
            if index >= len(tokens):
                break
            path = tokens[index]
            index += 1
        else:
            path = tokens[index]
            index += 1
        result.append((path, status))
    return result


def git_changed_files(project: Path) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for args in (
        ("diff", "--name-status", "-z"),
        ("diff", "--cached", "--name-status", "-z"),
    ):
        result = _git(project, *args)
        if result is not None and result.returncode == 0:
            pairs.extend(_parse_name_status(result.stdout))
    untracked = _git(project, "ls-files", "--others", "--exclude-standard", "-z")
    if untracked is not None and untracked.returncode == 0:
        pairs.extend((path, "??") for path in _decode_nul(untracked.stdout))

    dedup: Dict[str, str] = {}
    for path, status in pairs:
        normalized = Path(path.replace("\\", "/")).as_posix().lstrip("./")
        if normalized:
            dedup[normalized] = status
    return sorted(dedup.items())


def _formal_asset(path: Path, normalized: str) -> bool:
    parts = {part.lower() for part in Path(normalized).parts}
    name = path.name.lower()
    return bool(parts & FORMAL_SEGMENTS) or name.startswith("readme") or name in {"changelog.md", "license", "license.md"}


def scan_source_hygiene(project: Path, changed_files: Sequence[str] = (), clean: bool = False) -> Dict[str, object]:
    discovered = dict(git_changed_files(project))
    if changed_files:
        pairs = []
        for raw in changed_files:
            normalized = Path(raw.replace("\\", "/")).as_posix().lstrip("./")
            pairs.append((normalized, discovered.get(normalized, "EXPLICIT")))
    else:
        pairs = list(discovered.items())

    findings: List[Dict[str, object]] = []
    deleted: List[str] = []
    scanned: List[str] = []
    for raw, status in pairs:
        target = _inside(project, raw)
        normalized = Path(raw.replace("\\", "/")).as_posix().lstrip("./")
        if target is None:
            findings.append({"path": normalized, "code": "PATH_OUTSIDE_PROJECT", "resolution": "BLOCK"})
            continue
        if not target.exists() or not target.is_file() or target.is_symlink():
            continue
        scanned.append(normalized)
        formal = _formal_asset(target, normalized)
        newly_added = status == "??" or status.startswith("A")
        safe_file = newly_added and not formal and target.suffix.lower() in SAFE_TEMP_SUFFIXES
        text = ""
        if target.suffix.lower() in TEXT_SUFFIXES and target.stat().st_size <= 1024 * 1024:
            text = target.read_text(encoding="utf-8", errors="replace")
        marker_file = not formal and "HARNESS_TEMPORARY_FILE" in text
        if safe_file or marker_file:
            if clean:
                target.unlink()
                deleted.append(normalized)
                continue
            findings.append({"path": normalized, "code": "SAFE_TEMPORARY_FILE", "resolution": "CLEANABLE"})
            continue
        if TEMP_NAME_RE.match(target.name) and not formal:
            findings.append({"path": normalized, "code": "AMBIGUOUS_TEMPORARY_FILENAME", "resolution": "REVIEW"})
        if text:
            for code, pattern in PATTERNS:
                if pattern.search(text):
                    resolution = "PRESERVE_FORMAL_ASSET" if formal else "REVIEW"
                    findings.append({"path": normalized, "code": code, "resolution": resolution})

    unresolved = [item for item in findings if item["resolution"] in {"BLOCK", "REVIEW", "CLEANABLE"}]
    return {
        "gate": "source_hygiene",
        "gate_status": "PASS" if not unresolved else "BLOCKED",
        "scanned_files": sorted(set(scanned)),
        "deleted_files": sorted(deleted),
        "findings": findings,
        "claim_boundary": "CHANGED_FILE_HYGIENE_ONLY_NOT_GENERAL_CODE_QUALITY",
    }
