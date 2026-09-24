#!/usr/bin/env python3
"""Risk-based security posture gate for new and legacy projects.

This gate does not prescribe token authentication for every system. It requires
security requirements to match the actual exposure, data, authentication model,
and change risk. Legacy debt is triaged rather than pretending all historical
vulnerabilities can be fixed in one ticket.
"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Mapping

PROJECT_STAGES = {"NEW", "LEGACY"}
RISKS = {"T0", "T1", "T2", "T3"}
EXPOSURES = {"LOCAL", "INTERNAL", "PARTNER", "INTERNET"}
SENSITIVITY = {"LOW", "MEDIUM", "HIGH", "RESTRICTED"}
AUTH_MODELS = {"NONE", "SESSION", "TOKEN", "OIDC_OAUTH", "MIXED", "UNKNOWN"}
CONTROL_STATUSES = {"PASS", "GAP", "NOT_APPLICABLE", "UNKNOWN"}
POSTURE_STATUSES = {"BASELINE_READY", "DEBT_ACCEPTED", "REMEDIATION_REQUIRED", "NEEDS_REVIEW"}
CONTROL_KEYS = {
    "threat_model",
    "security_requirements",
    "authentication",
    "authorization",
    "token_validation",
    "session_management",
    "input_validation",
    "secrets_management",
    "security_logging",
    "dependency_management",
    "data_protection",
}


def _control(controls: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = controls.get(key)
    return value if isinstance(value, dict) else {}


def evaluate_security_posture(record: Mapping[str, object]) -> Dict[str, object]:
    errors: List[str] = []
    warnings: List[str] = []
    stage = record.get("project_stage")
    risk = record.get("change_risk")
    exposure = record.get("exposure")
    sensitivity = record.get("data_sensitivity")
    auth_model = record.get("auth_model")
    posture = record.get("status")
    reason = str(record.get("reason", "")).strip()
    if stage not in PROJECT_STAGES:
        errors.append("SECURITY_PROJECT_STAGE_INVALID")
    if risk not in RISKS:
        errors.append("SECURITY_CHANGE_RISK_INVALID")
    if exposure not in EXPOSURES:
        errors.append("SECURITY_EXPOSURE_INVALID")
    if sensitivity not in SENSITIVITY:
        errors.append("SECURITY_DATA_SENSITIVITY_INVALID")
    if auth_model not in AUTH_MODELS:
        errors.append("SECURITY_AUTH_MODEL_INVALID")
    if posture not in POSTURE_STATUSES:
        errors.append("SECURITY_POSTURE_STATUS_INVALID")
    if len(reason) < 12:
        errors.append("SECURITY_REASON_TOO_SHORT")

    controls = record.get("controls")
    if not isinstance(controls, dict):
        controls = {}
        errors.append("SECURITY_CONTROLS_REQUIRED")
    for key in CONTROL_KEYS:
        item = _control(controls, key)
        status = item.get("status")
        if status not in CONTROL_STATUSES:
            errors.append("SECURITY_CONTROL_STATUS_INVALID=" + key)
        if status in {"PASS", "GAP"} and len(str(item.get("evidence", "")).strip()) < 5:
            errors.append("SECURITY_CONTROL_EVIDENCE_REQUIRED=" + key)

    high_change = risk in {"T2", "T3"}
    high_exposure = exposure in {"PARTNER", "INTERNET"}
    sensitive = sensitivity in {"HIGH", "RESTRICTED"}

    if stage == "NEW" and high_change:
        for key in ("threat_model", "security_requirements", "authorization", "secrets_management", "input_validation"):
            if _control(controls, key).get("status") != "PASS":
                errors.append("NEW_PROJECT_SECURITY_BASELINE_REQUIRED=" + key)
        if auth_model == "UNKNOWN":
            errors.append("NEW_PROJECT_AUTH_MODEL_MUST_BE_DECIDED")
        if auth_model != "NONE" and _control(controls, "authentication").get("status") != "PASS":
            errors.append("NEW_PROJECT_AUTHENTICATION_REQUIRED")
        if auth_model in {"TOKEN", "OIDC_OAUTH", "MIXED"} and _control(controls, "token_validation").get("status") != "PASS":
            errors.append("TOKEN_VALIDATION_REQUIRED_FOR_SELECTED_AUTH_MODEL")
        if auth_model in {"SESSION", "MIXED"} and _control(controls, "session_management").get("status") != "PASS":
            errors.append("SESSION_MANAGEMENT_REQUIRED_FOR_SELECTED_AUTH_MODEL")

    vulnerabilities = record.get("known_vulnerabilities")
    if not isinstance(vulnerabilities, list):
        vulnerabilities = []
    unresolved_blockers = []
    for index, item in enumerate(vulnerabilities):
        if not isinstance(item, dict):
            errors.append(f"SECURITY_VULNERABILITY_INVALID={index}")
            continue
        severity = item.get("severity")
        status = item.get("status")
        if severity not in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}:
            errors.append(f"SECURITY_VULNERABILITY_SEVERITY_INVALID={index}")
            continue
        if status not in {"OPEN", "MITIGATED", "ACCEPTED", "NOT_REPRODUCED"}:
            errors.append(f"SECURITY_VULNERABILITY_STATUS_INVALID={index}")
            continue
        if status in {"OPEN", "ACCEPTED"}:
            if len(str(item.get("owner", "")).strip()) < 2:
                errors.append(f"SECURITY_VULNERABILITY_OWNER_REQUIRED={index}")
            due = str(item.get("due_date", "")).strip()
            try:
                date.fromisoformat(due)
            except ValueError:
                errors.append(f"SECURITY_VULNERABILITY_DUE_DATE_INVALID={index}")
            relevant = item.get("relevant_to_change") is True
            if severity in {"HIGH", "CRITICAL"} and relevant and (high_exposure or sensitive) and status == "OPEN":
                unresolved_blockers.append(str(item.get("id", index)))

    if posture == "NEEDS_REVIEW":
        errors.append("SECURITY_REVIEW_UNRESOLVED")
    if stage == "LEGACY" and not vulnerabilities and posture in {"DEBT_ACCEPTED", "REMEDIATION_REQUIRED"}:
        errors.append("LEGACY_SECURITY_DEBT_REQUIRES_INVENTORY")
    if unresolved_blockers:
        errors.append("SECURITY_RELEVANT_HIGH_RISK_OPEN=" + ",".join(unresolved_blockers))
    if stage == "LEGACY" and posture == "BASELINE_READY" and any(_control(controls, key).get("status") == "GAP" for key in CONTROL_KEYS):
        warnings.append("LEGACY_BASELINE_READY_HAS_RECORDED_GAPS")

    return {
        "gate": "security_posture",
        "gate_status": "PASS" if not errors else "BLOCKED",
        "errors": errors,
        "warnings": warnings,
        "project_stage": stage,
        "change_risk": risk,
        "auth_model": auth_model,
        "open_relevant_high_risk": unresolved_blockers,
        "claim_boundary": "RISK_BASED_SECURITY_READINESS_ONLY_NOT_PENETRATION_TEST_OR_VULNERABILITY_ABSENCE",
    }
