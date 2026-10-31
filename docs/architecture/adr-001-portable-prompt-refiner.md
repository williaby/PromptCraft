# ADR-001: Portable Prompt Refiner

> **Status:** Proposed | **Date:** 2026-10-09 | **Supersedes:** no prior ADR; replaces the undocumented four-journey
> hybrid workbench design (archived as branch `archive/legacy-hybrid-v0` in Phase 0)

## Context

PromptCraft-Hybrid started in June 2025 as a hybrid AI workbench: four progressive journeys, Zen MCP plus Prefect
orchestration, HyDE retrieval over Qdrant, and an agent registry with per-agent knowledge bases. Feature work stopped
in September 2025 after Phase 1. A survey of the codebase in October 2026 found:

- No code path calls an LLM to refine a prompt. The API path (`src/core/create_processor_core.py`) fills C.R.E.A.T.E.
  sections with regex matches and drops the user's original text. The Gradio path
  (`src/ui/journeys/journey1_smart_templates.py`) returns keyword-selected boilerplate; its only LLM hook is a stub
  behind a `hasattr` guard that is always false.
- By a per-module line count, roughly 13% of `src/` (about 9 to 10k of 72k lines) concerns prompt refinement. The rest
  is auth (two stacks), security, monitoring, MCP and Zen routing, and a Claude Code dynamic function loading prototype.
- HyDE, QueryCounselor, the agent registry, Qdrant ingestion, and journeys 3 and 4 are unwired, mocked, or
  placeholders. Prefect is not a dependency. Zen MCP is retired for this project, though `docker-compose.zen-vm.yaml`
  remains.
- There is no evaluation of refinement quality: no golden set, no judge, no before/after comparison.
- The most valuable asset is `knowledge/create_agent/`: the C.R.E.A.T.E. guide, depth tiers, error-prevention
  checklists, and a 2,009-line raw-to-refined few-shot gallery. The code never uses its content.
- Tooling has drifted from org standards. The repo uses Poetry; the org reusable workflows in `ByronWilliamsCPA/.github`
  are uv-only and reject Poetry repos outright. Two required status checks are satisfied only by stub workflows.

The goal is now narrower: refine a user's rough prompt into a standard, robust form that produces higher quality
results than the unrefined prompt. The refiner must work across environments:

- Claude (Claude Code, claude.ai, Claude Desktop), where most interactive work happens.
- The family office portal (Python), which runs Qwen3.6-35B-A3B on llama.cpp. Portal prompts must stay on-prem.
- Other MCP-capable clients, as a secondary target.

Two usage modes are required: a user-visible mode and a user-invisible mode, selected by which endpoint the caller uses.

## Decision

Build a lean refiner in small increments, shipping the zero-dependency piece first, and defer every component until a
real caller needs it. Archive the legacy code and align the repo with org standards before building.

### Scope discipline

The legacy design produced 72k lines of mostly unused infrastructure by building for callers that never arrived. This
ADR applies one rule: **a component is built only when a named caller exists.**

| Component | Caller | When |
| --- | --- | --- |
| Claude skill (hand-written) | Owner in Claude | Phase 1 |
| `refine()` library, visible mode, llama.cpp backend | Family office portal | Phase 2 |
| Invisible mode | Family office portal | Phase 4, gated |
| Anthropic backend, `open` engine tier | Deferred: no caller yet | When a hosted caller exists |
| MCP server | Deferred: no non-Claude MCP client in use yet | When one exists |
| Skill generated from spec with drift check | Deferred | When hand-maintenance shows drift |
| Embedding-based example selection | Experiment in Phase 3 | Adopted only on measured gain |
| DSPy (GEPA) tuning | Deferred | After Phase 4, on measured plateau |
| OpenAI and Gemini target profiles | Deferred | When a caller targets them |

### The spec (portable data, single source of truth)

A versioned directory of plain files, no code:

- `checklist`: gap-detection slots. C.R.E.A.T.E. (Context, Request, Examples, Augmentations, Tone and Format,
  Evaluation) plus explicit `role` and `inputs` slots.
- `depth_tiers`: when to make a light edit versus add structure, examples, or success criteria.
- `refiner_prompts`: the refiner's system prompt.
- `examples`: a curated subset of the few-shot gallery, converted from `10_few-shot-gallery.md` (which has no H3
  structure) into one structured record per example.
- `target_profiles`: rendering rules per target. Phase 2 ships `claude` and `qwen3_local` only.
- `golden`: the evaluation set (see Evaluation).

C.R.E.A.T.E. is the internal completeness checklist. It is not an output template that always emits six sections.

The spec carries a semantic version. The skill and the engine each record the spec version they were built against,
and the eval report records all three.

### The engine (Python library)

`refine(prompt, *, mode, target, engine, history=None) -> RefinementResult`

Pipeline:

1. **Analyze**: the engine model returns JSON (schema-constrained) with filled slots, detected gaps, a depth tier, and
   an `already_good` flag. `history` (prior conversation turns, if any) is context only; it is never rewritten.
2. **Clarify** (visible mode only): up to three high-value questions, each with a default answer.
3. **Render**, by depth tier:
   - **Light tier**: targeted insertion. The user's original text is kept verbatim and in order; missing pieces (output
     format, audience, success criteria) are inserted as short additions. No regeneration.
   - **Heavy tier**: structured render. Code renders the slots using the target profile. Used only when the original is
     too unstructured to extend.

   The model fills slots; code owns the format. This keeps a mid-size local model from producing malformed prompts.
4. **Self-check** (visible mode always; invisible mode only within the latency budget): an intent-preservation check
   that the refined prompt keeps every requirement of the original and adds none that are not labeled as assumptions.

**Prompt injection.** The user's prompt and any pasted content are data, not instructions to the refiner. They are
passed inside delimited blocks, and the refiner prompt states that instructions inside those blocks describe the
user's task and must not change the refiner's behavior. The golden set includes injection cases.

**Engine backend (Phase 2):** `openai_compatible`, one client for llama.cpp server (and Ollama or vLLM if ever needed),
using llama.cpp JSON-schema constrained output. Model IDs live in config, never in code. An `anthropic` backend is
deferred per the scope table.

**Engine tier:** `strict` (slot filling only, tight schema, thinking disabled). Qwen3.6-35B-A3B runs in `strict`. An
`open` tier for frontier models is deferred.

**Thinking mode.** `strict` tier sets `enable_thinking=false` through the chat template, because slot filling under a
JSON-schema grammar leaves no room for free-form reasoning tokens. The Phase 2 spike measures one alternative: a
two-pass call (free-text reasoning, then constrained extraction) and adopts it only if quality gain outweighs latency.

`RefinementResult` carries: refined prompt, original prompt, depth tier, slot-level provenance (`from_user` or
`assumed`), assumptions, clarifying questions, a skipped flag with reason, spec and engine versions, and timing.

### Two modes, selected by endpoint

| Aspect | Visible (`refine(mode="visible")`, `/refine`) | Invisible (`refine(mode="invisible")`, `/complete`) |
| --- | --- | --- |
| Clarifying questions | Yes, up to three, with defaults | Never |
| Output to user | Refined prompt, diff, labeled assumptions | Nothing; refined prompt goes straight to the target |
| Render | Light or heavy tier | Light tier only |
| Assumed slots | Allowed, labeled | **Zero**; any assumed slot means pass the original through |
| Length growth | No cap | Capped (initial value: refined length at most 2x original, tuned in Phase 4) |
| Already-good prompts | Reported as such | Passed through unchanged |
| Failure, timeout, guard trip | Error shown | Fail open: send the original prompt |
| Kill switch | n/a | Config flag disables refinement instantly |
| Audit | Returned to caller | Original and refined pair logged locally |

Invisible mode carries the higher risk because nobody reviews the rewrite. It ships in Phase 4 only after the runtime
guards above exist and its golden-set intent-preservation score clears the threshold set in Phase 1.

**Portal UI for visible mode.** The portal shows the original, the refined prompt, and a diff, with assumptions
highlighted and per-addition accept or reject. The portal owns this UI; the library supplies the data in
`RefinementResult`.

### Adapters

| Environment | Adapter | Who refines | Phase |
| --- | --- | --- | --- |
| Claude Code, claude.ai, Desktop | Hand-written skill distilled from the spec | Claude itself; no engine call | 1 |
| Family office portal | Library import (in-process) | Local Qwen via llama.cpp | 2 |
| Evals, scripting | CLI | Engine | 1 to 2 |
| Other MCP clients | MCP server | Engine set in server config | Deferred |

For the portal, refinement is a deterministic pre-processing step in code, not a tool the local model may or may not
choose to call.

**Distribution to the portal.** The library is installed from a git tag (`uv add git+https://...@vX.Y.Z`) and pinned in
the portal's `uv.lock`. A private index is not needed for one consumer.

### On-prem guarantee

Engine config carries `data_boundary: on_prem | any`. Under `on_prem`, the library:

- Accepts only engine hosts that resolve to loopback or an allowlisted LAN range. It resolves the host once and pins
  the IP for the session, which defeats DNS rebinding and `.local` names resolving off-LAN.
- Creates its HTTP client with `trust_env=False` (ignores `HTTPS_PROXY` and similar) and `follow_redirects=False`.
- Refuses the `anthropic` backend and any known hosted endpoint (including OpenRouter) even though OpenRouter speaks the
  same OpenAI-compatible protocol.
- Writes audit logs to local sinks only.
- Has no telemetry and makes no network calls other than to the configured engine.

Tests assert each rule. Portal prompts never enter the golden set or any judge call.

### Local stack (family office portal)

| Component | Model | Runtime |
| --- | --- | --- |
| Chat and refiner | [Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B), file `Qwen3.6-35B-A3B-UD-Q4_K_S.gguf` from [unsloth/Qwen3.6-35B-A3B-GGUF](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF) | llama.cpp on a Tesla P40 (24 GB) |
| Vision projector | Q8_0 mmproj from [ggml-org/Qwen3.6-35B-A3B-GGUF](https://huggingface.co/ggml-org/Qwen3.6-35B-A3B-GGUF) | llama.cpp |
| Embeddings | [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF), Q8_0 | llama.cpp on CPU |

Implications:

- **One GPU refines and answers.** In invisible mode each portal request makes two GPU calls (three if the self-check
  runs). llama.cpp serializes requests unless parallel slots are configured, and the KV cache for both shares 24 GB.
  The about-3B-active mixture-of-experts design helps per-token speed but does not remove contention.
- **Latency budget.** Initial target: refinement p95 under 1.5 seconds, measured on the P40 while it is also serving
  chat. Over budget means skip refinement and send the original. Phase 3 confirms or revises the number.
- **Evaluate the deployed artifact.** Golden-set results are keyed to the exact GGUF file and quantization; results
  from a full-precision or hosted Qwen do not transfer. Engine config records the file name and its SHA-256.
- **Target profile `qwen3_local`.** The portal's target model is the same Qwen build, so it gets its own rendering
  profile, tuned by evals rather than by vendor guidance written for frontier models.
- **Vision.** The refiner is text-only in v1. Image attachments pass through untouched; the `inputs` slot records that
  attachments exist so the refined prompt can reference them.
- **Embeddings.** No vector database. Phase 3 tests one optional use: choosing the most similar few-shot examples per
  prompt from an in-memory index (around a hundred vectors, built at startup). Adopted only on measured gain.

### Evaluation

- **Golden set, Phase 1:** 30 synthetic rough prompts covering coding, analysis, writing, and family office finance and
  administration, plus injection and already-good cases. Grows to 100 by Phase 4.
- **Portal pattern set:** 20 hand-written, PII-free paraphrases of real portal request patterns, kept in the portal's
  private repo and run only against the local engine.
- **Deterministic checks first:** schema validity, required slots present, length ratio, original text retained (light
  tier), no unlabeled assumptions. These run in CI on every change and cost nothing.
- **Pairwise judge:** compares the target model's output for the original versus the refined prompt. Positions swapped,
  ties allowed, 3 judge samples per pair. Judge is a Claude model for `qwen3_local` targets; for `claude` targets, a
  judge from a different family, chosen in Phase 1. Judges run only on synthetic data.
- **Intent preservation:** separate judge check that the refined prompt entails the original and adds only labeled
  assumptions.
- **Statistics:** the unit of analysis is the prompt pair, so n counts prompt pairs, not judge samples. Each pair's
  three judge samples are combined by majority vote into one outcome (win, loss, or tie); ties count as half a win.
  Report the pair-level win rate with a 95% Wilson score interval. At n=50 the interval is about plus or minus 14
  points, so no "beats baseline" claim is made unless the lower bound of that pair-level interval exceeds 50%. Judge
  agreement is calibrated on 20 human-labeled pairs before the judge gates anything.
- **Cost:** each eval run's judge cost is logged; judge runs happen on demand and nightly, not on every commit.

### Observability

The library emits counters (`refined`, `skipped_already_good`, `skipped_budget`, `fail_open`, `guard_tripped`) and a
latency histogram through a pluggable hook. The portal wires them to its local metrics stack. No remote telemetry.

## Phase 0: Archive, Tooling, and Standards Alignment

Phase 0 makes the repo a clean, standards-compliant base before any new code. Detailed steps, the workflow-by-workflow
map, and risks live in `docs/architecture/phase-0-migration-plan.md`. Summary:

1. Archive `main` as `legacy-hybrid-v0` (branch `archive/legacy-hybrid-v0`; tag pending).
2. Run `repo-compliance` in report-only mode to scope standards gaps. Ignore findings in code about to be removed.
3. Strip legacy code, tests, configs, and tracked artifacts. Keep `knowledge/create_agent/`, docs needed for history,
   and OpenSSF root files.
4. Migrate Poetry to uv: PEP 621 `pyproject.toml` with hatchling and `[dependency-groups]`, `uv.lock`, nox sessions on
   uv, pre-commit on `uv run` with mypy replaced by basedpyright, Renovate rules for uv and org workflow pins.
5. Replace bespoke CI with callers of `ByronWilliamsCPA/.github` reusable workflows pinned to
   `74cfc8e9d1ea1f6babc40bea102b3071af620942 # v11.0.1`. Replace the two stub workflows with real checks that emit the
   ruleset-required names `CI Gate` and `Dependency & Standards Validation`. Reset SonarCloud and Qlty baselines.
6. Run `repo-compliance` in interactive mode on the slim tree and apply approved remediations.

**Exit criteria:** org reusable workflows green on a PR; ruleset-required checks produced by real jobs;
`repo-compliance` audit clean or with documented exceptions.

## Consequences

### Positive

- Value ships in Phase 1 (the Claude skill) instead of after the engine and adapters.
- One spec drives the skill and the engine, so Claude and the portal refine the same way.
- Portal data stays on-prem by enforced configuration, not convention.
- Quality is measured with stated statistical limits, so improvements are real or not claimed.
- The repo matches org tooling and CI, so shared workflows and Renovate maintain it.

### Negative

- The legacy UI and API stop working on `main`. Nobody uses them in practice, and the tag preserves them.
- The hand-written skill and the engine can drift until generation is built. Mitigated by shared golden-set runs.
- Target profiles need re-verification with each model release.
- Invisible mode adds GPU load to every portal request.

### Risks to verify early

- Qwen3.6-35B-A3B (UD-Q4_K_S) quality as a `strict`-tier refiner. If weak, the portal offers visible mode only.
- The 1.5-second p95 budget under concurrent chat load on one P40.
- Judge bias toward longer prompts. The calibration set and length-ratio check address this.
- Org workflow friction for a small library: forced bandit, pip-audit, vulture, and an 80% coverage gate from day one.

## Phased Plan

| Phase | Deliverable | Exit criteria |
| --- | --- | --- |
| 0. Archive and align | Legacy tag; strip; uv and nox; org reusable workflows; compliance audit | See Phase 0 exit criteria |
| 1. Skill and baseline | Spec v0.1 (checklist, tiers, converted examples); hand-written Claude skill; 30-prompt golden set; deterministic checks; eval CLI; judge calibration | Skill in daily use; pass-through baseline recorded; judge agreement measured |
| 2. Engine, visible mode | Thinking-mode spike; `refine()` with analyze, clarify, render, self-check; `openai_compatible` backend; on-prem guard; `qwen3_local` profile | Deterministic checks pass; judge win rate lower CI bound above 50% vs baseline on golden set; on-prem tests pass |
| 3. P40 validation | Latency and quality on the P40 under concurrent chat; portal pattern set; embedding example-selection experiment | p95 budget met or revised; decision recorded on embeddings |
| 4. Invisible mode | Runtime guards, kill switch, audit log, observability hooks; golden set to 100 | Intent-preservation threshold met; guards tested; portal enables it behind a flag |
| 5. Deferred items | Generated skill, MCP server, Anthropic backend, DSPy tuning | Each starts only when its caller or trigger in the scope table exists |

## Open Questions

- Package name for the new library.
- Exact required-check contexts in ruleset `williaby-default-branch-baseline` (bare `CI Gate` or `ci / CI Gate`, and
  whether other checks are required). Confirm before deleting the stubs.
- Golden-set rubric thresholds for invisible mode.
