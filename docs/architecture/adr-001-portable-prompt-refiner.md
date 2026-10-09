# ADR-001: Portable Prompt Refiner

> **Status:** Proposed | **Date:** 2026-10-09 | **Supersedes:** the four-journey hybrid workbench design

## Context

PromptCraft-Hybrid started in June 2025 as a hybrid AI workbench: four progressive journeys, Zen MCP plus Prefect
orchestration, HyDE retrieval over Qdrant, and an agent registry with per-agent knowledge bases. Feature work stopped
in September 2025 after Phase 1. A survey of the codebase in October 2026 found:

- No code path calls an LLM to refine a prompt. The API path (`src/core/create_processor_core.py`) fills C.R.E.A.T.E.
  sections with regex matches and drops the user's original text. The Gradio path
  (`src/ui/journeys/journey1_smart_templates.py`) returns keyword-selected boilerplate; its only LLM hook is a stub
  behind an always-false guard.
- Roughly 13% of `src/` (about 9 to 10k of 72k lines) concerns prompt refinement. The rest is auth (two stacks),
  security, monitoring, MCP and Zen routing, and a Claude Code dynamic function loading prototype.
- HyDE, QueryCounselor, the agent registry, Qdrant ingestion, and journeys 3 and 4 are unwired, mocked, or
  placeholders. Prefect is not a dependency. Zen MCP is retired.
- There is no evaluation of refinement quality: no golden set, no judge, no before/after comparison.
- The most valuable asset is `knowledge/create_agent/`: the C.R.E.A.T.E. guide, depth tiers, error-prevention
  checklists, and a large raw-to-refined few-shot gallery. The code never uses its content.

The goal is now narrower: refine a user's rough prompt into a standard, robust form that produces higher quality
results than the unrefined prompt. The refiner must work across environments:

- Claude (Claude Code, claude.ai, Claude Desktop), where most interactive work happens.
- The family office portal (Python), which runs Qwen3.6-35B-A3B on llama.cpp. Portal prompts must stay on-prem.
- Other MCP-capable clients, as a secondary target.

Two usage modes were part of the original intent and remain required: a user-visible mode and a user-invisible mode,
selected by which endpoint the caller uses.

## Decision

Build a new, lean refiner as three layers. Archive the legacy code.

### Layer 1: The spec (portable data, single source of truth)

A versioned directory of plain files, no code:

- `checklist`: gap-detection slots. C.R.E.A.T.E. (Context, Request, Examples, Augmentations, Tone and Format,
  Evaluation) plus explicit `role` and `inputs` slots.
- `depth_tiers`: when to make a light edit versus add structure, examples, or success criteria.
- `refiner_prompts`: the refiner's system prompt, one variant per engine tier (see below).
- `examples`: a curated subset of `knowledge/create_agent/10_*` few-shot pairs.
- `target_profiles`: rendering rules per target model family (Claude, OpenAI reasoning models, Gemini, Qwen and other
  local models).
- `golden`: the evaluation set (rough prompt, rubric, optional reference output). Synthetic content only, so it can be
  judged by any model without leaking portal data.

C.R.E.A.T.E. is the internal completeness checklist. It is not an output template that always emits six sections.

### Layer 2: The engine (Python library)

`refine(prompt, *, mode, target, engine) -> RefinementResult`

Pipeline:

1. **Analyze**: the engine model returns JSON (schema-constrained) with filled slots, detected gaps, a complexity tier,
   and an `already_good` flag.
2. **Clarify** (visible mode only): up to three high-value questions with default answers.
3. **Render**: deterministic Python code renders the slots into the final prompt using the target profile. The model
   fills slots; code owns the format. This keeps small local models from producing malformed prompts and makes every
   engine testable the same way.
4. **Self-check**: an intent-preservation check that the refined prompt keeps every requirement of the original and
   adds none that are not labeled as assumptions.

Engine backends:

- `openai_compatible`: one client for llama.cpp server, Ollama, vLLM, and OpenRouter. Uses llama.cpp JSON schema
  constrained output.
- `anthropic`: native Anthropic SDK.
- Model IDs live in config, never in code.

Engine tiers: `strict` (small or local models: slot filling only, tight schema) and `open` (frontier models: may
rewrite phrasing). Qwen3.6-35B-A3B starts in `strict`; evals decide whether it can move to `open`.

`RefinementResult` carries: refined prompt, original prompt, slot-level provenance (`from_user` or `assumed`), a list
of assumptions, clarifying questions, a skipped flag with reason, engine and spec versions, and timing.

### Two modes, selected by endpoint

| Aspect | Visible (`/refine`, `refine(mode="visible")`) | Invisible (`/complete`, `refine(mode="invisible")`) |
| --- | --- | --- |
| Clarifying questions | Yes, up to three, with defaults | Never |
| Output to user | Refined prompt, diff, labeled assumptions | Nothing; refined prompt goes straight to the target |
| Edit strength | Tier-appropriate | Conservative: minimal edits, no invented requirements |
| Already-good prompts | Reported as such | Passed through unchanged |
| Failure or timeout | Error shown | Fail open: send the original prompt |
| Audit | Returned to caller | Original and refined pair logged locally |

Invisible mode carries the higher risk because nobody reviews the rewrite. It ships only after its intent-preservation
score on the golden set clears a threshold set in Phase 1.

### Layer 3: Adapters

| Environment | Adapter | Who refines |
| --- | --- | --- |
| Claude Code, claude.ai, Desktop | Skill generated from the spec | Claude itself; no engine call |
| Family office portal | Library import (in-process) | Local Qwen via llama.cpp |
| Other MCP clients | MCP server (stdio and streamable HTTP) | Engine set in server config |
| Evals, scripting | CLI | Any engine |

The skill is generated from the spec by a build step. CI fails if the committed skill differs from a fresh build.

MCP is an adapter, not the backbone. For the portal, refinement is a deterministic pre-processing step in code, not a
tool the local model may or may not choose to call.

### On-prem guarantee

- Engine config carries `data_boundary: on_prem | any`. With `on_prem`, the library refuses any engine whose base URL
  is not loopback or an allowlisted LAN host, and refuses the `anthropic` backend outright.
- The library has no telemetry and makes no network calls other than to the configured engine.
- A test asserts that the portal profile cannot resolve to a remote engine.
- Portal prompts never enter the golden set or any judge call.

### Local stack (family office portal)

| Component | Model | Runtime |
| --- | --- | --- |
| Chat and refiner | [Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B), file `Qwen3.6-35B-A3B-UD-Q4_K_S.gguf` from [unsloth/Qwen3.6-35B-A3B-GGUF](https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF) | llama.cpp on a Tesla P40 (24 GB) |
| Vision projector | Q8_0 mmproj from [ggml-org/Qwen3.6-35B-A3B-GGUF](https://huggingface.co/ggml-org/Qwen3.6-35B-A3B-GGUF) | llama.cpp |
| Embeddings | [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF), Q8_0 | llama.cpp on CPU |

Implications:

- **Same model refines and answers.** In invisible mode each portal request makes at least two calls to one GPU. The
  `already_good` short-circuit and a latency budget matter more than they would with a hosted engine. The A3B
  mixture-of-experts design (about 3B active parameters per token) should keep per-call latency workable on the P40;
  Phase 3 measures it.
- **Evaluate the deployed artifact.** Golden-set results are keyed to the exact GGUF file and quantization. Results from
  a full-precision or hosted Qwen do not transfer to the Q4_K_S build. Engine config records the model file name and
  its SHA-256.
- **Target profile `qwen3_local`.** The portal's target model is the same Qwen build, so it gets its own rendering
  profile, tuned by evals rather than by vendor guidance written for frontier models.
- **Thinking mode.** The analyze step is slot filling, which may not need reasoning. Phase 2's spike compares thinking
  on and off for quality, latency, and compatibility with llama.cpp schema-constrained output.
- **Vision.** The refiner is text-only in v1. Image attachments pass through untouched; the `inputs` slot records that
  attachments exist so the refined prompt can reference them.
- **Embeddings.** No vector database on the refine path. The embedding model has one optional use: selecting the few
  most similar few-shot examples for each prompt from an in-memory index of the spec's examples (around a hundred
  vectors, built at startup). This keeps the prompt short on a mid-size local model while keeping examples relevant.
  Static examples ship first; dynamic selection is adopted only if the golden set shows a gain. Embeddings may also
  serve a refinement cache for repeated prompts.

### Evaluation

- Golden set of 50 to 100 synthetic rough prompts covering the real use cases (coding, analysis, writing, family office
  finance and administration).
- Metrics per (engine, target) pair:
  - Pairwise judge: output of original versus refined prompt, positions swapped, ties allowed, judge from a different
    model family than the target.
  - Intent preservation: refined prompt entails the original and adds only labeled assumptions.
  - Deterministic checks: schema validity, required slots, length budget.
  - Skip accuracy: already-good prompts pass through.
- Runs from the CLI and in CI on any change to the spec or engine.
- Later: tune `refiner_prompts` offline with DSPy (GEPA) against the golden set.

### Legacy code

- Tag the current `main` as `legacy-hybrid-v0` so all history stays reachable.
- Remove from `main`: dynamic function loading and A/B framework, Zen and Docker MCP clients, agent registry and
  discovery, HyDE, QueryCounselor, Qdrant ingestion, journeys 1 to 4, Gradio UI, `auth_simple`, tracked `.db` files,
  `lint_env/`, `temp_cleanup/`, and the tests that cover removed code.
- Keep and migrate: `knowledge/create_agent/` content (into the spec), the OpenRouter client pattern (into the
  `openai_compatible` backend), FastAPI and the main `auth` stack only if a hosted endpoint needs them.
- Drop heavy dependencies the new core does not need: torch, transformers, sentence-transformers, qdrant-client,
  gradio, pandas, plotly. Core runtime dependencies target `httpx` and `pydantic`; `anthropic`, `mcp`, and `fastapi`
  become optional extras.

## Consequences

**Positive**

- One spec drives every environment, so Claude, the portal, and MCP clients refine the same way.
- Portal data stays on-prem by enforced configuration, not convention.
- Quality is measured, so changes to models or rules are regression-tested.
- The portal imports a small package without the current dependency tree.

**Negative**

- The legacy UI and API stop working on `main`. Nobody uses them in practice, and the tag preserves them.
- Per-target profiles need re-verification with each major model release.
- The local engine adds latency to every invisible-mode call. Requires a latency budget and the `already_good`
  short-circuit.

**Risks to verify early**

- Qwen3.6-35B-A3B (UD-Q4_K_S) quality as a refiner in `strict` tier. If the golden-set results are weak, the portal
  keeps invisible mode off and offers visible mode only.
- Interaction between Qwen thinking mode and llama.cpp schema-constrained output. Spike before building the engine.
- GPU contention on the single P40 when refinement and answering share it. Measure end-to-end latency in Phase 3.
- Judge bias toward longer prompts. Calibrate the judge on a small human-labeled subset.

## Phased Plan

| Phase | Deliverable | Exit criteria |
| --- | --- | --- |
| 0. Archive | Tag `legacy-hybrid-v0`; strip legacy code and deps; lean `pyproject.toml` | CI green on the slim tree |
| 1. Spec and evals | Spec format; distilled checklist, tiers, examples; golden set; eval CLI with a pass-through baseline | Baseline scores recorded |
| 2. Engine | Analyze, render, self-check; both backends; both modes; on-prem guard | Beats baseline on judge score; intent threshold met |
| 3. Local model validation | Qwen3.6-35B-A3B (UD-Q4_K_S) on the P40 in `strict` tier; latency budget; optional embedding-based example selection | Decision recorded on invisible mode for the portal |
| 4. Adapters | Generated Claude skill with drift check; MCP server; portal integration guide | Skill and engine agree on the golden set |
| 5. Optimize | DSPy GEPA tuning of refiner prompts per engine tier | Measured gain over Phase 2 |

Phase 3's thinking-mode and schema spike runs at the start of Phase 2, since it shapes the engine interface.

## Open Questions

- Package and repository naming for the new core, and whether it is published to a private index or installed from git.
- Whether a hosted HTTP endpoint is needed at all, or the portal's in-process import plus MCP covers every caller.
- Golden-set rubric thresholds for invisible mode.
