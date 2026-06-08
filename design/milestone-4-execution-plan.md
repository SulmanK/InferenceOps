# Milestone 4 Execution Plan: Optional Agentic Controller

## Purpose

Milestone 4 evaluates whether an LLM-style controller can make useful routing decisions after strong static and heuristic baselines already exist.

The goal is not to give an agent broad infrastructure control. The agent receives the same normalized observation schema as the heuristic controller and must choose one bounded policy action.

## Bounded Action Space

```text
set_policy in {round_robin, cache_aware, power_of_two}
```

Invalid actions are rejected and replaced with a safe fallback. Invalid action count and fallback count are first-class metrics.

## V0 Scope

Milestone 4 starts offline:

- Build a strict JSON action contract for the agent.
- Add deterministic scripted-agent mode for reproducible tests.
- Add optional OpenAI-compatible mode for real LLM calls later.
- Evaluate agent choices against the Milestone 2 policy comparison artifact.
- Compare against the Milestone 3 heuristic baseline.

No Lambda GPU instance is required for the first pass.

## Commands

Build or reuse a Milestone 2 comparison artifact:

```bash
python metrics/compare_m2_policies.py \
  --run-id 20260606T192505Z \
  --replay-dir artifacts/m2/replay \
  --out-dir C:\tmp\InferenceOps-m3
```

Run deterministic scripted-agent evaluation:

```bash
python controllers/evaluate_m4_agentic.py \
  --comparison C:\tmp\InferenceOps-m3\policy_comparison_20260606T192505Z.json \
  --agent-mode scripted \
  --out-dir C:\tmp\InferenceOps-m4
```

Optional real LLM mode:

```bash
set AGENT_OPENAI_API_KEY=<key>
set AGENT_MODEL=<model>
python controllers/evaluate_m4_agentic.py \
  --comparison C:\tmp\InferenceOps-m3\policy_comparison_20260606T192505Z.json \
  --agent-mode openai-compatible \
  --out-dir C:\tmp\InferenceOps-m4
```

## Done Means

- Agent output is parsed through a strict JSON contract.
- Agent actions are bounded and validated.
- Invalid output falls back to a safe policy and is recorded.
- Evaluation is deterministic in scripted mode.
- Real LLM mode, if used, runs at temperature 0.
- The agent is compared against the Milestone 3 heuristic baseline.

## Live Run Gate

Only run Lambda again if offline evaluation produces a useful result worth validating live. A live run should reuse `controllers/run_live_controller.py` after adding an agentic controller mode to that runner.
