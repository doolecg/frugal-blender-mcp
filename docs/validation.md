# Validation — 2026-10-13

Local environment: Windows 11, Blender **5.1.1**, Python **3.12.10**, MCP Python SDK **1.30.0**,
NVIDIA RTX 5060 Laptop GPU (OptiX).

Executed, not inferred:

- `uv run ruff check` and `uv run ruff format --check` — passed.
- Full pytest suite with `BLENDER_EXE` and `BLENDER_TEST_UI=1` — **34 passed**, no skips. New since
  2026-09-10: `install-addon` into a fake Blender config (newest version, explicit version, replace,
  missing-config error, ZIP contents), PowerShell UTF-8 BOM on CLI stdin, capture keeping the
  scene's aspect ratio (1920x1080 scene → 768x432 preview), EEVEE capture of a scene with no world
  plus the Cycles override (from #1), and lean tool definitions (no generated titles or `null`
  unions, at most 300 tokens).
- Wheel smoke test through `uvx --isolated --from dist/blender_astra_mcp-0.2.0-py3-none-any.whl`:
  `--version`, `--help` and `install-addon --zip`. The wheel bundles the add-on sources.
- [Tool-context benchmark](tool-context.md): this server's real `tools/list` against Blender Lab's
  official server and ahujasid's server, tokenized with `o200k_base` and `cl100k_base`.
- [Lighthouse example](../examples/lighthouse): the five batches replayed from an empty
  factory-startup scene in a fresh headless Blender — 109 operations, 5,017 argument tokens,
  202 result tokens, every batch under 0.1 s. The README animation was rendered from that scene.
- Add-on ZIP packaging and Python wheel/sdist build — passed.
- Actual ZIP installation into an isolated Blender scripts directory, enable, timer registration,
  start/stop, descriptor removal and disable — passed.
- Separate real Blender background process: registration, scene inspection, operation discovery,
  syntax prevalidation, dry run, partial failure reporting, authenticated request replay,
  linked-copy material isolation, deletion confirmation, path validation, read-only enforcement,
  refusal to edit unmanaged data, a 50-object camera render and `.blend` copy save.
- Official MCP SDK client over actual stdio: initialization, exactly four tools, discovery,
  execution, inspection and PNG image result, all forwarded to real Blender.
- Separate hidden interactive Blender process: actual timer-driven socket execution, Undo of a
  transform batch, timer removal and descriptor cleanup.
- Protocol tests: authentication before dispatch, malformed JSON, request size cap, replay conflict,
  bounded replay cache, loopback restriction and transport failure reporting.

## Payload microbenchmark

[Raw measured result](benchmark.json). The test runs the same 50 transforms individually and batched,
resets object positions between variants, and compares resulting object properties for equality.
Both variants use this project's own bridge, not a fabricated competing-server baseline.

| Metric | Individual | Batched |
|---|---:|---:|
| Calls | 50 | 1 |
| Argument tokens | 1,149 | 1,002 |
| Result tokens | 800 | 16 |
| Total payload tokens | 1,949 | 1,018 |

Tokenizer: `cl100k_base`. **47.77% payload reduction**. Tokens are counted over compact serialized
arguments/results, excluding transport authentication and IDs that are not model-visible.
It also excludes model reasoning, history, system prompts, caching/billing, protocol tool-call
envelopes, images, setup and discovery. No model was invoked or charged by this benchmark.

This does not establish the total token cost or output quality of an autonomous modeling task.
A future comparison should run repeated matched briefs on the same model/settings, collect the
provider's actual usage counters, and score scene/render correctness before comparing consumption.
The [tool-context benchmark](tool-context.md) compares fixed tool-definition cost against other
servers. It does not compare end-to-end task cost or output quality.

## Visual artifact

The lighthouse animation is a real Cycles render (960x540, 64 samples, 112 frames) of the scene the
five example batches build. Frames 97 to 112 are cross-faded into frames 1 to 16 so the GIF loops
without a visible seam. The scene was written by Claude across iterations with `capture` previews;
the committed batches are the final versions, not a single unedited agent transcript. It shows scene
construction, shading, animation and rendering, not production topology.

`artifacts/` is ignored because logs can contain local paths.

## Limits of verification

- Blender 4.2+, macOS and Linux behavior are not yet runtime-tested locally.
- CI runs Python checks and package builds; Blender-dependent tests explicitly skip unless a Blender
  executable is supplied. CI passing is not a substitute for the real local Blender tests above.
- This is not a complete security audit, performance stress test, or long-session reliability test.
- Background mode has no Undo guarantee; files and partial writes are not transactional.
