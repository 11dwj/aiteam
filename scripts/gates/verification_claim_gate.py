#!/usr/bin/env python3
"""Deterministic validation for tiered S/M/C verification declarations."""
from __future__ import annotations

from typing import Dict, List

TASK_CLASSES = {"S", "M", "C"}
SECURITY_LEVELS = {"NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL", "NEEDS_REVIEW"}
VERIFICATION_KINDS = {"STATIC_REVIEW", "COMPILE", "RUNTIME", "BUSINESS"}
RESULTS = {"PASS", "FAIL", "TEST_BLOCKED", "NOT_RUN", "NEEDS_REVIEW", "PARTIAL"}
BUSINESS_STATUSES = {"PASS", "FAIL", "TEST_BLOCKED", "NOT_RUN", "NEEDS_REVIEW"}
FEEDBACK_STATUSES = {"READY", "BLOCKED", "NOT_APPLICABLE"}
HANDOFF_STATUSES = {"READY_FOR_REVIEW", "READY_FOR_USER_TEST", "BLOCKED", "NEEDS_REVIEW", "DELIVERED"}

# These five fields are the irreducible complex-ticket verification declaration.
COMPLEX_REQUIRED_FIELDS = (
    "execution_subject",
    "target_entry",
    "command_or_entry",
    "assertions",
    "evidence_refs",
)

FOLLOW_UP = {
    "VERIFICATION_EXECUTION_SUBJECT_REQUIRED": "谁实际执行了本次验证？请标明维护者完整执行、外部完整复现、外部抽查、仅核对历史或本地 Agent 执行。",
    "VERIFICATION_TARGET_ENTRY_REQUIRED": "本次验证实际进入了哪个页面、API、任务入口或可执行函数？",
    "VERIFICATION_COMMAND_OR_ENTRY_REQUIRED": "请提供实际执行的验证命令或人工入口动作。",
    "VERIFICATION_ASSERTIONS_REQUIRED": "请列出至少一个可观察断言；复杂工单还必须包含一个反例或失败路径断言。",
    "VERIFICATION_EVIDENCE_REFS_REQUIRED": "请提供项目内 harness/evidence/ 下可复核的证据路径。",
    "COMPLEX_NEGATIVE_ASSERTION_REQUIRED": "复杂工单的断言中缺少 NEGATIVE 或 FAILURE_PATH 反例。",
    "SECURITY_IMPACT_REASON_REQUIRED": "请说明本次变更为何无安全影响，或具体影响了认证、授权、数据、外网入口、上传下载、依赖或日志中的哪一项。",
    "SECURITY_IMPACT_NEEDS_REVIEW": "安全影响尚未确定；请先完成影响判断再声明完成。",
    "SECURITY_EVIDENCE_REF_REQUIRED": "高/严重安全影响必须提供 security-posture 或风险接受证据路径。",
    "TICKET_FEEDBACK_SOURCE_MISMATCH": "反馈衔接中的 source_ticket_id 必须与当前工单一致。",
    "TICKET_FEEDBACK_SUMMARY_REQUIRED": "请写一段可直接进入日终反馈或负责人交接的脱敏摘要。",
    "TECHNICAL_RESULT_CANNOT_CLAIM_BUSINESS_PASS": "静态检查或编译通过不能声明业务 PASS；请改为 NOT_RUN/NEEDS_REVIEW，或补真实入口和业务断言验证。",
    "BUSINESS_PASS_REQUIRES_TARGET_ENTRY_EXECUTED": "业务 PASS 必须确认真实目标入口已经执行。",
    "BUSINESS_PASS_REQUIRES_ASSERTIONS_EXECUTED": "业务 PASS 必须确认业务断言已经执行。",
    "HISTORICAL_REVIEW_CANNOT_CLAIM_BUSINESS_PASS": "仅核对历史证据不能声明当前候选包业务 PASS。",
}


def _non_empty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(_non_empty(item) for item in value)


def _append(errors: List[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _assertion_types(assertions: object) -> set[str]:
    if not isinstance(assertions, list):
        return set()
    types: set[str] = set()
    for item in assertions:
        if isinstance(item, dict) and _non_empty(item.get("type")):
            types.add(str(item["type"]).strip().upper())
        elif isinstance(item, str):
            upper = item.upper()
            if upper.startswith("NEGATIVE:") or upper.startswith("FAILURE_PATH:"):
                types.add("NEGATIVE")
            elif item.strip():
                types.add("POSITIVE")
    return types


def evaluate_verification_claim(record: object) -> Dict[str, object]:
    """Validate structure and claim boundaries; never execute tests or assert business truth."""
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(record, dict):
        return {
            "gate_status": "BLOCKED",
            "errors": ["VERIFICATION_CLAIM_INPUT_NOT_OBJECT"],
            "warnings": [],
            "follow_up_questions": [],
            "claim_boundary": "DECLARATION_VALIDATION_ONLY_NOT_BUSINESS_PASS",
        }

    if record.get("schema_version") != "1.0":
        _append(errors, "VERIFICATION_CLAIM_SCHEMA_VERSION_INVALID")
    ticket_id = record.get("ticket_id")
    if not _non_empty(ticket_id):
        _append(errors, "VERIFICATION_CLAIM_TICKET_ID_REQUIRED")
    task_class = record.get("task_class")
    if task_class not in TASK_CLASSES:
        _append(errors, "VERIFICATION_TASK_CLASS_INVALID")
    if not _non_empty(record.get("classification_reason")):
        _append(errors, "VERIFICATION_CLASSIFICATION_REASON_REQUIRED")

    security = record.get("security_impact")
    if not isinstance(security, dict):
        _append(errors, "SECURITY_IMPACT_REQUIRED")
        security = {}
    security_level = security.get("level")
    if security_level not in SECURITY_LEVELS:
        _append(errors, "SECURITY_IMPACT_LEVEL_INVALID")
    if not _non_empty(security.get("reason")):
        _append(errors, "SECURITY_IMPACT_REASON_REQUIRED")
    if not isinstance(security.get("triggers", []), list):
        _append(errors, "SECURITY_IMPACT_TRIGGERS_INVALID")
    if security_level == "NEEDS_REVIEW":
        _append(errors, "SECURITY_IMPACT_NEEDS_REVIEW")
    if security_level in {"HIGH", "CRITICAL"} and not _non_empty(security.get("evidence_ref")):
        _append(errors, "SECURITY_EVIDENCE_REF_REQUIRED")

    claim = record.get("verification_claim")
    if not isinstance(claim, dict):
        _append(errors, "VERIFICATION_CLAIM_REQUIRED")
        claim = {}
    kind = claim.get("verification_kind")
    result = claim.get("result")
    claimed_business = claim.get("claimed_business_status")
    if kind not in VERIFICATION_KINDS:
        _append(errors, "VERIFICATION_KIND_INVALID")
    if result not in RESULTS:
        _append(errors, "VERIFICATION_RESULT_INVALID")
    if claimed_business not in BUSINESS_STATUSES:
        _append(errors, "CLAIMED_BUSINESS_STATUS_INVALID")
    for field in ("target_entry_executed", "business_assertions_executed"):
        if not isinstance(claim.get(field), bool):
            _append(errors, f"{field.upper()}_BOOLEAN_REQUIRED")
    if not isinstance(claim.get("not_verified"), list):
        _append(errors, "VERIFICATION_NOT_VERIFIED_LIST_REQUIRED")

    # S keeps the declaration small. M/C progressively require real entry and assertion detail.
    if task_class == "S":
        if not _non_empty(claim.get("execution_subject")):
            _append(errors, "VERIFICATION_EXECUTION_SUBJECT_REQUIRED")
        if not _non_empty_list(claim.get("evidence_refs")):
            _append(errors, "VERIFICATION_EVIDENCE_REFS_REQUIRED")
    elif task_class in {"M", "C"}:
        required_codes = {
            "execution_subject": "VERIFICATION_EXECUTION_SUBJECT_REQUIRED",
            "target_entry": "VERIFICATION_TARGET_ENTRY_REQUIRED",
            "command_or_entry": "VERIFICATION_COMMAND_OR_ENTRY_REQUIRED",
            "assertions": "VERIFICATION_ASSERTIONS_REQUIRED",
            "evidence_refs": "VERIFICATION_EVIDENCE_REFS_REQUIRED",
        }
        for field in COMPLEX_REQUIRED_FIELDS:
            value = claim.get(field)
            present = _non_empty_list(value) if field in {"assertions", "evidence_refs"} else _non_empty(value)
            if not present:
                _append(errors, required_codes[field])
        if task_class == "C" and _non_empty_list(claim.get("assertions")):
            types = _assertion_types(claim.get("assertions"))
            if not ({"NEGATIVE", "FAILURE_PATH"} & types):
                _append(errors, "COMPLEX_NEGATIVE_ASSERTION_REQUIRED")
        if not claim.get("not_verified"):
            warnings.append("M_OR_C_NOT_VERIFIED_LIST_EMPTY_CONFIRM_SCOPE_IS_COMPLETE")

    # Claim boundary: technical checks remain technical regardless of wording.
    if kind in {"STATIC_REVIEW", "COMPILE"} and claimed_business in {"PASS", "FAIL"}:
        _append(errors, "TECHNICAL_RESULT_CANNOT_CLAIM_BUSINESS_PASS" if claimed_business == "PASS" else "TECHNICAL_RESULT_CANNOT_CLAIM_BUSINESS_FAIL")
    if claimed_business == "PASS":
        if kind not in {"RUNTIME", "BUSINESS"}:
            _append(errors, "BUSINESS_PASS_REQUIRES_RUNTIME_OR_BUSINESS_VERIFICATION")
        if claim.get("target_entry_executed") is not True:
            _append(errors, "BUSINESS_PASS_REQUIRES_TARGET_ENTRY_EXECUTED")
        if claim.get("business_assertions_executed") is not True:
            _append(errors, "BUSINESS_PASS_REQUIRES_ASSERTIONS_EXECUTED")
        if str(claim.get("execution_subject", "")).strip().upper() == "HISTORICAL_REVIEW":
            _append(errors, "HISTORICAL_REVIEW_CANNOT_CLAIM_BUSINESS_PASS")
        if result != "PASS":
            _append(errors, "BUSINESS_PASS_REQUIRES_PASS_RESULT")

    feedback = record.get("ticket_feedback")
    if not isinstance(feedback, dict):
        _append(errors, "TICKET_FEEDBACK_LINK_REQUIRED")
        feedback = {}
    if _non_empty(ticket_id) and feedback.get("source_ticket_id") != ticket_id:
        _append(errors, "TICKET_FEEDBACK_SOURCE_MISMATCH")
    if feedback.get("handoff_status") not in HANDOFF_STATUSES:
        _append(errors, "TICKET_HANDOFF_STATUS_INVALID")
    if feedback.get("feedback_status") not in FEEDBACK_STATUSES:
        _append(errors, "TICKET_FEEDBACK_STATUS_INVALID")
    if not _non_empty(feedback.get("summary")):
        _append(errors, "TICKET_FEEDBACK_SUMMARY_REQUIRED")
    if not isinstance(feedback.get("unresolved_items"), list):
        _append(errors, "TICKET_FEEDBACK_UNRESOLVED_ITEMS_LIST_REQUIRED")
    if task_class == "C" and feedback.get("feedback_status") == "NOT_APPLICABLE":
        _append(errors, "COMPLEX_TICKET_FEEDBACK_CANNOT_BE_NOT_APPLICABLE")

    follow_up_questions = [FOLLOW_UP[code] for code in errors if code in FOLLOW_UP]
    technical_status = "NOT_RUN"
    if result in {"PASS", "FAIL", "TEST_BLOCKED", "NEEDS_REVIEW"}:
        technical_status = result
    elif result == "PARTIAL":
        technical_status = "PARTIAL"

    return {
        "gate_status": "PASS" if not errors else "BLOCKED",
        "task_class": task_class,
        "technical_status": technical_status,
        "claimed_business_status": claimed_business,
        "errors": errors,
        "warnings": warnings,
        "follow_up_questions": follow_up_questions,
        "required_complex_fields": list(COMPLEX_REQUIRED_FIELDS),
        "claim_boundary": "DECLARATION_VALIDATION_ONLY_NOT_BUSINESS_PASS",
    }
