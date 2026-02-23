# Work Order: Hermes 4.3 Master System Prompt Rollout

## Objective
Deploy a production-ready master system prompt for `FBM-AI` with strict tool-calling behavior, deterministic JSON outputs, and operational safeguards suitable for AI-gateway validation.

## Scope
- Add a canonical prompt artifact at `services/ai-orchestrator/prompts/system.prompt.ts`.
- Define acceptance criteria for safe tool invocation and schema compliance.
- Provide a phased rollout plan aligned to LangGraph multi-agent orchestration.

## Repo Reality Check
This repository is primarily Python/Rust and does not currently contain a TypeScript service tree for `services/ai-orchestrator`.

To satisfy the requested target location and support future orchestrator extraction, this work order introduces the path and prompt artifact as a self-contained module.

## Improved Plan (Production-Grade)

### Phase 1 — Prompt Baseline (Complete in this change)
1. Create canonical prompt module exporting `SYSTEM_PROMPT`.
2. Add hidden deterministic guardrails:
   - correctness > creativity
   - never break JSON schema
   - never fabricate IDs/tool state
3. Separate response modes:
   - conversational plaintext
   - strict JSON tool mode
4. Add explicit destructive-action confirmation policy.
5. Add domain-specific workflows (onboarding, product, import, finance, localization, error handling).

### Phase 2 — Gateway Contract Hardening
1. Mirror prompt output contract in gateway validators.
2. Reject mixed-mode outputs (JSON + prose).
3. Reject unknown keys in tool payloads.
4. Add telemetry tags:
   - `mode_selected`
   - `tool_call_attempted`
   - `schema_validation_result`

### Phase 3 — LangGraph Integration
1. Attach prompt to supervisor node entrypoint.
2. Add tool-routing policies per agent type.
3. Add preflight node for required-field checks.
4. Add human-confirmation gate for destructive actions.

### Phase 4 — QA & Safety Certification
1. Build red-team test set:
   - permission escalation attempts
   - fabricated ID pressure tests
   - destructive action without confirmation
2. Build schema-fuzz test set for malformed tool outputs.
3. Validate failure behavior:
   - asks for missing fields
   - no tool call on incomplete required params
4. Run deterministic replay tests for regression control.

### Phase 5 — Controlled Launch
1. Enable for internal vendor sandbox only.
2. Compare against baseline KPIs:
   - tool-call success rate
   - invalid-schema rate
   - onboarding completion time
   - product draft acceptance rate
3. Progressive rollout by traffic percentage.
4. Define rollback switch at gateway layer.

## Work Breakdown Structure

### WO-1: Prompt Artifact Delivery
- **Owner:** AI Platform
- **Deliverable:** `system.prompt.ts` with master prompt export
- **Dependencies:** none
- **Exit Criteria:** file compiles as a plain TS module; prompt includes explicit output-mode contract

### WO-2: Gateway Validation Alignment
- **Owner:** AI Gateway
- **Deliverable:** strict schema checks + mixed-mode rejection
- **Dependencies:** WO-1
- **Exit Criteria:** invalid tool payloads rejected with structured error code

### WO-3: LangGraph Supervisor Wiring
- **Owner:** Orchestrator Team
- **Deliverable:** supervisor prompt binding + preflight/checkpoint nodes
- **Dependencies:** WO-1, WO-2
- **Exit Criteria:** destructive actions always require explicit confirmation checkpoint

### WO-4: Test Harness & Red-Team Pack
- **Owner:** QA / Applied AI Safety
- **Deliverable:** prompt conformance suite + adversarial scenarios
- **Dependencies:** WO-2, WO-3
- **Exit Criteria:** zero high-severity policy violations in certification run

### WO-5: Gradual Production Rollout
- **Owner:** Product Operations
- **Deliverable:** staged rollout with KPI dashboard + rollback playbook
- **Dependencies:** WO-4
- **Exit Criteria:** KPI thresholds met for two consecutive release windows

## Acceptance Criteria
1. Prompt always produces either plaintext OR strict JSON, never both.
2. Tool actions contain only `action` and `parameters` keys.
3. Destructive operations are blocked without explicit vendor confirmation.
4. Missing required fields trigger clarification prompts, not speculative tool calls.
5. Prompt refuses unauthorized operations and provides a safe alternative.

## Risks & Mitigations
- **Risk:** Model drifts into mixed-mode responses.
  - **Mitigation:** gateway regex/schema enforcement + conformance tests.
- **Risk:** Fabricated IDs under pressure prompts.
  - **Mitigation:** deterministic self-check + red-team cases.
- **Risk:** Overly verbose responses increase vendor friction.
  - **Mitigation:** style constraints + response-length monitoring.

## Definition of Done
- Prompt module exists at requested path.
- Work order recorded in-repo with phases, owners, and acceptance criteria.
- Ready for downstream gateway and LangGraph implementation.
