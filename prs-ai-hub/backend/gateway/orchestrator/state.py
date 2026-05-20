from typing import Any, TypedDict


class PRSState(TypedDict, total=False):
    request_id: str
    submitted_at: str
    requestor_data: dict[str, Any]
    vendor_data: dict[str, Any]
    contract_text: str
    contract_filename: str
    sku_items: list[dict[str, Any]]
    addendum_text: str

    requestor_result: dict[str, Any] | None
    vendor_result: dict[str, Any] | None
    parties_result: dict[str, Any] | None
    commercial_result: dict[str, Any] | None
    legal_result: dict[str, Any] | None
    sku_schedule_result: dict[str, Any] | None
    sku_policy_result: dict[str, Any] | None

    overall_status: str | None
    critical_blockers: list[str]
    warnings: list[str]
    requires_human_review: bool
    next_action: str | None
    review_time_estimate: str | None
    agent_results: dict[str, Any]
    agents: dict[str, str]
    error: str | None
