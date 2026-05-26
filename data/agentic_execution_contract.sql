-- ============================================================
-- Agentic Execution Contract Schema — SQLite DDL
-- Generated from AgenticExecutionContractSchema-2026-05-21
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ============================================================
-- CORE: AGENT & PRINCIPAL
-- ============================================================

CREATE TABLE IF NOT EXISTS AGENT (
    agent_uuid          TEXT NOT NULL PRIMARY KEY,
    name                TEXT NOT NULL,
    description         TEXT,
    domain              TEXT,
    lifecycle_status    TEXT,
    default_maturity_level TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS PRINCIPAL (
    principal_uuid  TEXT NOT NULL PRIMARY KEY,
    display_name    TEXT NOT NULL,
    principal_type  TEXT,
    email           TEXT,
    external_ref    TEXT
);

CREATE TABLE IF NOT EXISTS AGENT_OWNERSHIP (
    agent_uuid          TEXT NOT NULL REFERENCES AGENT(agent_uuid),
    principal_uuid      TEXT NOT NULL REFERENCES PRINCIPAL(principal_uuid),
    responsibility_role TEXT,
    effective_from      TEXT,
    effective_to        TEXT,
    PRIMARY KEY (agent_uuid, principal_uuid)
);

-- ============================================================
-- CONTRACT
-- ============================================================

CREATE TABLE IF NOT EXISTS RUNTIME_CONTRACT (
    agent_uuid                  TEXT NOT NULL REFERENCES AGENT(agent_uuid),
    contract_uuid               TEXT NOT NULL,
    contract_version            TEXT,
    maturity_level              TEXT,
    status                      TEXT,
    content_hash                TEXT,
    is_immutable                INTEGER NOT NULL DEFAULT 0 CHECK (is_immutable IN (0,1)),
    immutable_from              TEXT,
    effective_from              TEXT,
    effective_to                TEXT,
    supersedes_contract_uuid    TEXT REFERENCES RUNTIME_CONTRACT(contract_uuid),
    created_by_principal_uuid   TEXT REFERENCES PRINCIPAL(principal_uuid),
    created_at                  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (agent_uuid, contract_uuid)
);

-- ============================================================
-- RUNTIME PROFILE & LIMITS
-- ============================================================

CREATE TABLE IF NOT EXISTS RUNTIME_PROFILE (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    runtime_profile_uuid TEXT NOT NULL,
    sandbox_mode        TEXT,
    isolation_level     TEXT,
    network_policy      TEXT,
    state_reset_policy  TEXT,
    residue_policy      TEXT,
    teardown_policy     TEXT,
    deny_by_default     INTEGER NOT NULL DEFAULT 0 CHECK (deny_by_default IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, runtime_profile_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS RUNTIME_LIMIT (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    limit_uuid          TEXT NOT NULL,
    limit_scope         TEXT,
    resource_type       TEXT,
    limit_value         REAL,
    unit                TEXT,
    enforcement_action  TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, limit_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

-- ============================================================
-- PHASES & TRANSITIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS CONTRACT_PHASE (
    agent_uuid           TEXT NOT NULL,
    contract_uuid        TEXT NOT NULL,
    phase_uuid           TEXT NOT NULL,
    phase_code           TEXT,
    phase_name           TEXT,
    sequence_number      INTEGER,
    entry_criteria       TEXT,
    exit_criteria        TEXT,
    max_iterations       INTEGER,
    timeout_seconds      INTEGER,
    default_failure_mode TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, phase_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS PHASE_TRANSITION (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    transition_uuid     TEXT NOT NULL,
    from_phase_uuid     TEXT REFERENCES CONTRACT_PHASE(phase_uuid),
    to_phase_uuid       TEXT REFERENCES CONTRACT_PHASE(phase_uuid),
    allowed_condition   TEXT,
    max_retries         INTEGER,
    timeout_seconds     INTEGER,
    on_failure_action   TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, transition_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

-- ============================================================
-- COGNITIVE ROLES
-- ============================================================

CREATE TABLE IF NOT EXISTS COGNITIVE_ROLE (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    role_uuid               TEXT NOT NULL,
    role_name               TEXT,
    description             TEXT,
    responsibility          TEXT,
    trace_required          INTEGER NOT NULL DEFAULT 0 CHECK (trace_required IN (0,1)),
    memory_scope_strategy   TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, role_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS PHASE_ROLE_BINDING (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    phase_uuid          TEXT NOT NULL,
    role_uuid           TEXT NOT NULL,
    invocation_order    INTEGER,
    required            INTEGER NOT NULL DEFAULT 0 CHECK (required IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, phase_uuid, role_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, phase_uuid) REFERENCES CONTRACT_PHASE(agent_uuid, contract_uuid, phase_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, role_uuid) REFERENCES COGNITIVE_ROLE(agent_uuid, contract_uuid, role_uuid)
);

-- ============================================================
-- MODELS & BINDINGS
-- ============================================================

CREATE TABLE IF NOT EXISTS MODEL (
    agent_uuid      TEXT NOT NULL,
    contract_uuid   TEXT NOT NULL,
    model_uuid      TEXT NOT NULL,
    provider        TEXT,
    model_name      TEXT,
    model_version   TEXT,
    model_type      TEXT,
    modality        TEXT,
    cost_tier       TEXT,
    deployment_ref  TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, model_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS ROLE_MODEL_BINDING (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    role_model_uuid     TEXT NOT NULL,
    role_uuid           TEXT REFERENCES COGNITIVE_ROLE(role_uuid),
    phase_uuid          TEXT REFERENCES CONTRACT_PHASE(phase_uuid),
    model_uuid          TEXT REFERENCES MODEL(model_uuid),
    purpose             TEXT,
    temperature         REAL,
    max_tokens          INTEGER,
    policy_constraints  TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, role_model_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS MODEL_FALLBACK (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    fallback_uuid       TEXT NOT NULL,
    role_model_uuid     TEXT REFERENCES ROLE_MODEL_BINDING(role_model_uuid),
    fallback_model_uuid TEXT REFERENCES MODEL(model_uuid),
    trigger_condition   TEXT,
    priority_order      INTEGER,
    PRIMARY KEY (agent_uuid, contract_uuid, fallback_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

-- ============================================================
-- RESOURCES & TYPED DETAILS
-- ============================================================

CREATE TABLE IF NOT EXISTS RESOURCE (
    agent_uuid      TEXT NOT NULL,
    contract_uuid   TEXT NOT NULL,
    resource_uuid   TEXT NOT NULL,
    resource_type   TEXT,
    name            TEXT,
    description     TEXT,
    owner_team      TEXT,
    risk_level      TEXT,
    version         TEXT,
    enabled         INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, resource_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS TOOL_DETAILS (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    resource_uuid       TEXT NOT NULL,
    tool_type           TEXT,
    idempotent          INTEGER NOT NULL DEFAULT 0 CHECK (idempotent IN (0,1)),
    input_schema_ref    TEXT,
    output_schema_ref   TEXT,
    validation_policy   TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, resource_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, resource_uuid) REFERENCES RESOURCE(agent_uuid, contract_uuid, resource_uuid)
);

CREATE TABLE IF NOT EXISTS API_DETAILS (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    resource_uuid       TEXT NOT NULL,
    service_name        TEXT,
    endpoint_ref        TEXT,
    method              TEXT,
    auth_scheme         TEXT,
    request_schema_ref  TEXT,
    response_schema_ref TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, resource_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, resource_uuid) REFERENCES RESOURCE(agent_uuid, contract_uuid, resource_uuid)
);

CREATE TABLE IF NOT EXISTS DATA_DETAILS (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    resource_uuid       TEXT NOT NULL,
    data_domain         TEXT,
    classification      TEXT,
    retention_class     TEXT,
    provenance_required INTEGER NOT NULL DEFAULT 0 CHECK (provenance_required IN (0,1)),
    masking_rule_ref    TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, resource_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, resource_uuid) REFERENCES RESOURCE(agent_uuid, contract_uuid, resource_uuid)
);

CREATE TABLE IF NOT EXISTS KNOWLEDGE_DETAILS (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    resource_uuid       TEXT NOT NULL,
    source_type         TEXT,
    trust_tier          TEXT,
    freshness_sla       TEXT,
    version_policy      TEXT,
    citation_required   INTEGER NOT NULL DEFAULT 0 CHECK (citation_required IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, resource_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, resource_uuid) REFERENCES RESOURCE(agent_uuid, contract_uuid, resource_uuid)
);

CREATE TABLE IF NOT EXISTS MEMORY_DETAILS (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    resource_uuid       TEXT NOT NULL,
    memory_type         TEXT,
    boundary_scope      TEXT,
    compression_policy  TEXT,
    anchoring_policy    TEXT,
    default_ttl_seconds INTEGER,
    PRIMARY KEY (agent_uuid, contract_uuid, resource_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, resource_uuid) REFERENCES RESOURCE(agent_uuid, contract_uuid, resource_uuid)
);

CREATE TABLE IF NOT EXISTS INTEGRATION_DETAILS (
    agent_uuid           TEXT NOT NULL,
    contract_uuid        TEXT NOT NULL,
    resource_uuid        TEXT NOT NULL,
    system_name          TEXT,
    endpoint_type        TEXT,
    protocol             TEXT,
    resilience_pattern   TEXT,
    compensation_action  TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, resource_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, resource_uuid) REFERENCES RESOURCE(agent_uuid, contract_uuid, resource_uuid)
);

-- ============================================================
-- PHASE RESOURCE GRANTS
-- ============================================================

CREATE TABLE IF NOT EXISTS PHASE_RESOURCE_GRANT (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    phase_uuid              TEXT NOT NULL,
    resource_uuid           TEXT NOT NULL,
    access_mode             TEXT,
    operation_scope         TEXT,
    max_calls_per_run       INTEGER,
    rate_limit_per_minute   INTEGER,
    requires_approval       INTEGER NOT NULL DEFAULT 0 CHECK (requires_approval IN (0,1)),
    approval_gate_uuid      TEXT,   -- FK to APPROVAL_GATE added after that table
    retry_policy            TEXT,
    circuit_breaker_policy  TEXT,
    filter_expression       TEXT,
    denial_action           TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, phase_uuid, resource_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, phase_uuid)    REFERENCES CONTRACT_PHASE(agent_uuid, contract_uuid, phase_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, resource_uuid) REFERENCES RESOURCE(agent_uuid, contract_uuid, resource_uuid)
);

-- ============================================================
-- CONTEXT RULES
-- ============================================================

CREATE TABLE IF NOT EXISTS CONTEXT_RULE (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    context_rule_uuid   TEXT NOT NULL,
    phase_uuid          TEXT REFERENCES CONTRACT_PHASE(phase_uuid),
    layer_type          TEXT,
    injection_order     INTEGER,
    saliency_filter     TEXT,
    sensitivity_filter  TEXT,
    max_tokens          INTEGER,
    redaction_policy    TEXT,
    drift_detection_rule TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, context_rule_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

-- ============================================================
-- POLICIES & RULES
-- ============================================================

CREATE TABLE IF NOT EXISTS POLICY (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    policy_uuid         TEXT NOT NULL,
    policy_name         TEXT,
    policy_type         TEXT,
    policy_version      TEXT,
    immutable_hash      TEXT,
    status              TEXT,
    source_of_authority TEXT,
    effective_from      TEXT,
    effective_to        TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, policy_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS POLICY_RULE (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    policy_rule_uuid    TEXT NOT NULL,
    policy_uuid         TEXT REFERENCES POLICY(policy_uuid),
    rule_code           TEXT,
    condition_expr      TEXT,
    decision            TEXT,
    enforcement_point   TEXT,
    severity            TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, policy_rule_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS PHASE_POLICY_BINDING (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    phase_uuid              TEXT NOT NULL,
    policy_uuid             TEXT NOT NULL,
    enforcement_mode        TEXT,
    priority_order          INTEGER,
    required_evidence_level TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, phase_uuid, policy_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, phase_uuid)  REFERENCES CONTRACT_PHASE(agent_uuid, contract_uuid, phase_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, policy_uuid) REFERENCES POLICY(agent_uuid, contract_uuid, policy_uuid)
);

-- ============================================================
-- GUARDRAILS
-- ============================================================

CREATE TABLE IF NOT EXISTS GUARDRAIL (
    agent_uuid      TEXT NOT NULL,
    contract_uuid   TEXT NOT NULL,
    guardrail_uuid  TEXT NOT NULL,
    guardrail_name  TEXT,
    trigger_type    TEXT,
    condition_expr  TEXT,
    risk_threshold  REAL,
    enabled         INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, guardrail_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS APPROVAL_GATE (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    approval_gate_uuid  TEXT NOT NULL,
    gate_name           TEXT,
    approver_role       TEXT,
    risk_level          TEXT,
    required_quorum     INTEGER,
    timeout_seconds     INTEGER,
    on_timeout_action   TEXT,
    evidence_required   INTEGER NOT NULL DEFAULT 0 CHECK (evidence_required IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, approval_gate_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS PHASE_GUARDRAIL_BINDING (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    phase_uuid              TEXT NOT NULL,
    guardrail_uuid          TEXT NOT NULL,
    enforcement_point       TEXT,
    action_code             TEXT,
    approval_gate_uuid      TEXT REFERENCES APPROVAL_GATE(approval_gate_uuid),
    telemetry_event_name    TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, phase_uuid, guardrail_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, phase_uuid)     REFERENCES CONTRACT_PHASE(agent_uuid, contract_uuid, phase_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, guardrail_uuid) REFERENCES GUARDRAIL(agent_uuid, contract_uuid, guardrail_uuid)
);

-- ============================================================
-- IDENTITY & CREDENTIALS
-- ============================================================

CREATE TABLE IF NOT EXISTS IDENTITY_PROFILE (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    identity_profile_uuid   TEXT NOT NULL,
    profile_name            TEXT,
    identity_provider       TEXT,
    credential_type         TEXT,
    task_bound              INTEGER NOT NULL DEFAULT 0 CHECK (task_bound IN (0,1)),
    default_ttl_seconds     INTEGER,
    PRIMARY KEY (agent_uuid, contract_uuid, identity_profile_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS PHASE_CREDENTIAL_GRANT (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    phase_uuid              TEXT NOT NULL,
    identity_profile_uuid   TEXT NOT NULL,
    privilege_name          TEXT,
    privilege_scope         TEXT,
    issue_on_entry          INTEGER NOT NULL DEFAULT 0 CHECK (issue_on_entry IN (0,1)),
    revoke_on_exit          INTEGER NOT NULL DEFAULT 0 CHECK (revoke_on_exit IN (0,1)),
    max_ttl_seconds         INTEGER,
    PRIMARY KEY (agent_uuid, contract_uuid, phase_uuid, identity_profile_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, phase_uuid)           REFERENCES CONTRACT_PHASE(agent_uuid, contract_uuid, phase_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, identity_profile_uuid) REFERENCES IDENTITY_PROFILE(agent_uuid, contract_uuid, identity_profile_uuid)
);

-- ============================================================
-- OBSERVABILITY & TELEMETRY
-- ============================================================

CREATE TABLE IF NOT EXISTS OBSERVABILITY_EVENT_TYPE (
    agent_uuid      TEXT NOT NULL,
    contract_uuid   TEXT NOT NULL,
    event_type_uuid TEXT NOT NULL,
    event_name      TEXT,
    event_category  TEXT,
    schema_ref      TEXT,
    required_fields TEXT,
    pii_handling    TEXT,
    retention_class TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, event_type_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS PHASE_TELEMETRY_REQUIREMENT (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    phase_uuid          TEXT NOT NULL,
    event_type_uuid     TEXT NOT NULL,
    required            INTEGER NOT NULL DEFAULT 0 CHECK (required IN (0,1)),
    sample_rate         REAL,
    correlation_keys    TEXT,
    evidence_level      TEXT,
    sink_ref            TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, phase_uuid, event_type_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, phase_uuid)      REFERENCES CONTRACT_PHASE(agent_uuid, contract_uuid, phase_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, event_type_uuid) REFERENCES OBSERVABILITY_EVENT_TYPE(agent_uuid, contract_uuid, event_type_uuid)
);

CREATE TABLE IF NOT EXISTS AUDIT_RETENTION_RULE (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    retention_rule_uuid TEXT NOT NULL,
    event_type_uuid     TEXT REFERENCES OBSERVABILITY_EVENT_TYPE(event_type_uuid),
    retention_days      INTEGER,
    legal_hold_supported INTEGER NOT NULL DEFAULT 0 CHECK (legal_hold_supported IN (0,1)),
    storage_location    TEXT,
    access_policy_ref   TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, retention_rule_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

-- ============================================================
-- PROTOCOLS
-- ============================================================

CREATE TABLE IF NOT EXISTS PROTOCOL (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    protocol_uuid           TEXT NOT NULL,
    protocol_name           TEXT,
    protocol_type           TEXT,
    protocol_version        TEXT,
    schema_ref              TEXT,
    provenance_required     INTEGER NOT NULL DEFAULT 0 CHECK (provenance_required IN (0,1)),
    policy_manifest_required INTEGER NOT NULL DEFAULT 0 CHECK (policy_manifest_required IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, protocol_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS PROTOCOL_FIELD_REQUIREMENT (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    protocol_field_uuid TEXT NOT NULL,
    protocol_uuid       TEXT REFERENCES PROTOCOL(protocol_uuid),
    field_name          TEXT,
    data_type           TEXT,
    required            INTEGER NOT NULL DEFAULT 0 CHECK (required IN (0,1)),
    validation_rule     TEXT,
    carries_provenance  INTEGER NOT NULL DEFAULT 0 CHECK (carries_provenance IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, protocol_field_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS PEER_AGENT (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    peer_agent_uuid     TEXT NOT NULL,
    peer_agent_name     TEXT,
    trust_domain        TEXT,
    capability_ref      TEXT,
    contact_protocol    TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, peer_agent_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS PROTOCOL_BINDING (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    protocol_binding_uuid   TEXT NOT NULL,
    phase_uuid              TEXT REFERENCES CONTRACT_PHASE(phase_uuid),
    protocol_uuid           TEXT REFERENCES PROTOCOL(protocol_uuid),
    direction               TEXT,
    peer_agent_uuid         TEXT REFERENCES PEER_AGENT(peer_agent_uuid),
    required_context_fields TEXT,
    verification_policy     TEXT,
    on_verification_failure TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, protocol_binding_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

-- ============================================================
-- DELEGATION
-- ============================================================

CREATE TABLE IF NOT EXISTS DELEGATION_RULE (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    delegation_rule_uuid TEXT NOT NULL,
    phase_uuid          TEXT REFERENCES CONTRACT_PHASE(phase_uuid),
    peer_agent_uuid     TEXT REFERENCES PEER_AGENT(peer_agent_uuid),
    capability_required TEXT,
    max_depth           INTEGER,
    approval_gate_uuid  TEXT REFERENCES APPROVAL_GATE(approval_gate_uuid),
    handoff_state_policy TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, delegation_rule_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

-- ============================================================
-- STATE MACHINE
-- ============================================================

CREATE TABLE IF NOT EXISTS STATE_MACHINE (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    state_machine_uuid      TEXT NOT NULL,
    name                    TEXT,
    initial_state_code      TEXT,
    final_state_codes       TEXT,
    state_persistence_policy TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, state_machine_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS WORKFLOW_STATE (
    agent_uuid          TEXT NOT NULL,
    contract_uuid       TEXT NOT NULL,
    state_uuid          TEXT NOT NULL,
    state_machine_uuid  TEXT REFERENCES STATE_MACHINE(state_machine_uuid),
    state_code          TEXT,
    description         TEXT,
    is_terminal         INTEGER NOT NULL DEFAULT 0 CHECK (is_terminal IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, state_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS WORKFLOW_TRANSITION (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    workflow_transition_uuid TEXT NOT NULL,
    state_machine_uuid      TEXT REFERENCES STATE_MACHINE(state_machine_uuid),
    from_state_uuid         TEXT REFERENCES WORKFLOW_STATE(state_uuid),
    to_state_uuid           TEXT REFERENCES WORKFLOW_STATE(state_uuid),
    trigger_event           TEXT,
    guard_condition         TEXT,
    action_on_transition    TEXT,
    PRIMARY KEY (agent_uuid, contract_uuid, workflow_transition_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

-- ============================================================
-- FEEDBACK
-- ============================================================

CREATE TABLE IF NOT EXISTS FEEDBACK_CHANNEL (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    feedback_channel_uuid   TEXT NOT NULL,
    channel_name            TEXT,
    signal_type             TEXT,
    source                  TEXT,
    update_target           TEXT,
    human_review_required   INTEGER NOT NULL DEFAULT 0 CHECK (human_review_required IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, feedback_channel_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

CREATE TABLE IF NOT EXISTS PHASE_FEEDBACK_RULE (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    phase_uuid              TEXT NOT NULL,
    feedback_channel_uuid   TEXT NOT NULL,
    capture_condition       TEXT,
    learning_mode           TEXT,
    apply_when              TEXT,
    max_delay_seconds       INTEGER,
    audit_required          INTEGER NOT NULL DEFAULT 0 CHECK (audit_required IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, phase_uuid, feedback_channel_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, phase_uuid)          REFERENCES CONTRACT_PHASE(agent_uuid, contract_uuid, phase_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid, feedback_channel_uuid) REFERENCES FEEDBACK_CHANNEL(agent_uuid, contract_uuid, feedback_channel_uuid)
);

-- ============================================================
-- CONTRACT VALIDATION TESTS
-- ============================================================

CREATE TABLE IF NOT EXISTS CONTRACT_VALIDATION_TEST (
    agent_uuid              TEXT NOT NULL,
    contract_uuid           TEXT NOT NULL,
    test_uuid               TEXT NOT NULL,
    test_name               TEXT,
    test_type               TEXT,
    target_component        TEXT,
    assertion_expr          TEXT,
    severity                TEXT,
    required_for_activation INTEGER NOT NULL DEFAULT 0 CHECK (required_for_activation IN (0,1)),
    PRIMARY KEY (agent_uuid, contract_uuid, test_uuid),
    FOREIGN KEY (agent_uuid, contract_uuid) REFERENCES RUNTIME_CONTRACT(agent_uuid, contract_uuid)
);

-- ============================================================
-- DEFERRED FK: approval_gate_uuid on PHASE_RESOURCE_GRANT
-- SQLite doesn't support ALTER TABLE ADD CONSTRAINT, so this
-- is enforced via application logic or a trigger if needed.
-- ============================================================

-- ============================================================
-- INDEXES (common query patterns)
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_runtime_contract_agent        ON RUNTIME_CONTRACT(agent_uuid);
CREATE INDEX IF NOT EXISTS idx_contract_phase_contract       ON CONTRACT_PHASE(agent_uuid, contract_uuid);
CREATE INDEX IF NOT EXISTS idx_resource_contract             ON RESOURCE(agent_uuid, contract_uuid);
CREATE INDEX IF NOT EXISTS idx_policy_contract               ON POLICY(agent_uuid, contract_uuid);
CREATE INDEX IF NOT EXISTS idx_guardrail_contract            ON GUARDRAIL(agent_uuid, contract_uuid);
CREATE INDEX IF NOT EXISTS idx_workflow_state_machine        ON WORKFLOW_STATE(state_machine_uuid);
CREATE INDEX IF NOT EXISTS idx_workflow_transition_states    ON WORKFLOW_TRANSITION(from_state_uuid, to_state_uuid);
CREATE INDEX IF NOT EXISTS idx_phase_role_binding_phase      ON PHASE_ROLE_BINDING(agent_uuid, contract_uuid, phase_uuid);
CREATE INDEX IF NOT EXISTS idx_role_model_binding_role       ON ROLE_MODEL_BINDING(role_uuid);
CREATE INDEX IF NOT EXISTS idx_phase_resource_grant_phase    ON PHASE_RESOURCE_GRANT(agent_uuid, contract_uuid, phase_uuid);
CREATE INDEX IF NOT EXISTS idx_observability_event_contract  ON OBSERVABILITY_EVENT_TYPE(agent_uuid, contract_uuid);
CREATE INDEX IF NOT EXISTS idx_feedback_channel_contract     ON FEEDBACK_CHANNEL(agent_uuid, contract_uuid);
CREATE INDEX IF NOT EXISTS idx_delegation_rule_phase         ON DELEGATION_RULE(phase_uuid);
CREATE INDEX IF NOT EXISTS idx_protocol_binding_phase        ON PROTOCOL_BINDING(phase_uuid);
