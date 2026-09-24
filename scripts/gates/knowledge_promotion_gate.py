#!/usr/bin/env python3
"""Deterministic gate for task experience candidates and controlled promotion.

NO_CANDIDATE is the normal outcome. A single observation may enter the review
pool as CANDIDATE, but promotion to project/company knowledge requires repeated
or high-severity evidence and explicit human approval.
"""
from __future__ import annotations

from typing import Dict, List, Mapping

STATUSES = {"NO_CANDIDATE", "CANDIDATE", "PROMOTED", "REJECTED", "NEEDS_REVIEW"}
SCOPES = {"NONE", "PROJECT", "COMPANY"}
TRIGGERS = {
    "REPEATED_SAME_PROJECT",
    "CROSS_PROJECT",
    "HIGH_SEVERITY_INCIDENT",
    "MEASURABLE_REWORK_REDUCTION",
    "DETERMINISTIC_CONTROL",
    "COMMON_FAILURE_MODE",
}


def _strings(value: object) -> List[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return []
    return [item.strip() for item in value if item.strip()]


def evaluate_knowledge_promotion(record: Mapping[str, object]) -> Dict[str, object]:
    errors: List[str] = []
    warnings: List[str] = []
    status = record.get("status")
    target_scope = record.get("target_scope")
    reason = str(record.get("reason", "")).strip()
    if status not in STATUSES:
        errors.append("KNOWLEDGE_STATUS_INVALID")
    if target_scope not in SCOPES:
        errors.append("KNOWLEDGE_SCOPE_INVALID")
    if len(reason) < 12:
        errors.append("KNOWLEDGE_REASON_TOO_SHORT")

    if status == "NO_CANDIDATE":
        if target_scope != "NONE":
            errors.append("NO_CANDIDATE_SCOPE_MUST_BE_NONE")
        return {
            "gate": "knowledge_promotion",
            "gate_status": "PASS" if not errors else "BLOCKED",
            "errors": errors,
            "warnings": warnings,
            "promotion_status": status,
            "claim_boundary": "NO_SUMMARY_REQUIRED_WHEN_NO_REUSABLE_CANDIDATE",
        }

    if status == "NEEDS_REVIEW":
        errors.append("KNOWLEDGE_REVIEW_UNRESOLVED")
    if status == "REJECTED" and target_scope == "NONE":
        return {
            "gate": "knowledge_promotion",
            "gate_status": "PASS" if not errors else "BLOCKED",
            "errors": errors,
            "warnings": warnings,
            "promotion_status": status,
            "claim_boundary": "REJECTED_CANDIDATE_RECORDED_WITHOUT_PROMOTION",
        }

    triggers = _strings(record.get("triggers"))
    invalid_triggers = sorted(set(triggers) - TRIGGERS)
    if invalid_triggers:
        errors.append("KNOWLEDGE_TRIGGER_INVALID=" + ",".join(invalid_triggers))
    if status in {"CANDIDATE", "PROMOTED"} and not triggers:
        errors.append("KNOWLEDGE_TRIGGER_REQUIRED")

    source_tasks = record.get("source_tasks")
    if not isinstance(source_tasks, list):
        source_tasks = []
    valid_sources = []
    project_ids = set()
    for index, item in enumerate(source_tasks):
        if not isinstance(item, dict):
            errors.append(f"KNOWLEDGE_SOURCE_INVALID={index}")
            continue
        project_id = str(item.get("project_id", "")).strip()
        task_ref = str(item.get("task_ref", "")).strip()
        evidence_ref = str(item.get("evidence_ref", "")).strip()
        if not project_id or not task_ref or not evidence_ref:
            errors.append(f"KNOWLEDGE_SOURCE_INCOMPLETE={index}")
            continue
        valid_sources.append(item)
        project_ids.add(project_id)
    if status in {"CANDIDATE", "PROMOTED"} and not valid_sources:
        errors.append("KNOWLEDGE_SOURCE_REQUIRED")

    candidate = record.get("candidate")
    if not isinstance(candidate, dict):
        errors.append("KNOWLEDGE_CANDIDATE_REQUIRED")
        candidate = {}
    for field in ("title", "problem_pattern", "proposed_control", "applicability", "non_applicability"):
        if len(str(candidate.get(field, "")).strip()) < 8:
            errors.append("KNOWLEDGE_CANDIDATE_FIELD_MISSING=" + field)
    if candidate.get("sanitized") is not True:
        errors.append("KNOWLEDGE_NOT_SANITIZED")
    if candidate.get("contains_project_secrets") is True:
        errors.append("KNOWLEDGE_CONTAINS_PROJECT_SECRETS")

    validation = record.get("validation")
    if not isinstance(validation, dict):
        validation = {}
        errors.append("KNOWLEDGE_VALIDATION_REQUIRED")
    runs = validation.get("independent_runs")
    if not isinstance(runs, int) or isinstance(runs, bool) or runs < 0:
        errors.append("KNOWLEDGE_INDEPENDENT_RUNS_INVALID")
        runs = 0
    measured = validation.get("benefit_measured") is True
    high_severity = "HIGH_SEVERITY_INCIDENT" in triggers

    if status == "CANDIDATE":
        if target_scope == "NONE":
            errors.append("CANDIDATE_SCOPE_CANNOT_BE_NONE")
        if target_scope == "PROJECT" and len(valid_sources) < 2 and not high_severity:
            warnings.append("PROJECT_CANDIDATE_NEEDS_MORE_EVIDENCE_BEFORE_PROMOTION")
        if target_scope == "COMPANY" and len(project_ids) < 2 and runs < 3:
            warnings.append("COMPANY_CANDIDATE_NEEDS_CROSS_PROJECT_OR_THREE_RUNS_BEFORE_PROMOTION")
        if target_scope == "COMPANY" and not measured and "DETERMINISTIC_CONTROL" not in triggers:
            warnings.append("COMPANY_CANDIDATE_VALUE_NOT_YET_MEASURED_OR_DETERMINISTIC")

    if status == "PROMOTED":
        if target_scope == "NONE":
            errors.append("PROMOTED_SCOPE_CANNOT_BE_NONE")
        elif target_scope == "PROJECT" and len(valid_sources) < 2 and not high_severity:
            errors.append("PROJECT_PROMOTION_NEEDS_REPETITION_OR_INCIDENT")
        elif target_scope == "COMPANY":
            if len(project_ids) < 2 and runs < 3:
                errors.append("COMPANY_PROMOTION_NEEDS_CROSS_PROJECT_OR_THREE_RUNS")
            if not measured and "DETERMINISTIC_CONTROL" not in triggers:
                errors.append("COMPANY_PROMOTION_NEEDS_MEASURED_OR_DETERMINISTIC_VALUE")

    decision = record.get("decision")
    if not isinstance(decision, dict):
        decision = {}
    if status == "PROMOTED":
        if len(str(decision.get("approved_by", "")).strip()) < 3:
            errors.append("KNOWLEDGE_PROMOTION_APPROVAL_REQUIRED")
        if len(str(decision.get("decision_ref", "")).strip()) < 5:
            errors.append("KNOWLEDGE_PROMOTION_DECISION_REF_REQUIRED")
    elif status == "CANDIDATE" and decision.get("approved_by"):
        warnings.append("CANDIDATE_HAS_APPROVER_BUT_IS_NOT_PROMOTED")

    return {
        "gate": "knowledge_promotion",
        "gate_status": "PASS" if not errors else "BLOCKED",
        "errors": errors,
        "warnings": warnings,
        "promotion_status": status,
        "target_scope": target_scope,
        "source_count": len(valid_sources),
        "project_count": len(project_ids),
        "claim_boundary": "CANDIDATE_COLLECTION_IS_NOT_PROMOTION_HUMAN_APPROVAL_REQUIRED",
    }
