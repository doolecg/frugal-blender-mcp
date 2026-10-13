# Fixed context cost of Blender MCP servers

Every MCP client sends the server's tool definitions (and any server instructions) to the model
before the first prompt, and again on every request after that. That cost is paid even when the
agent never touches Blender. This benchmark measures it.

Measured on 2026-10-13, Windows 11, tokenized with tiktoken. Raw output: [tool-context.json](tool-context.json).

| Server | Tools | Definition tokens | Instruction tokens | Total (o200k) | vs. this repo |
|---|---:|---:|---:|---:|---:|
| **Frugal Blender MCP** (this repo, 0.2.0) | **4** | 289 | 49 | **338** | 1x |
| [Blender Lab official](https://projects.blender.org/lab/blender_mcp) blender-mcp 1.0.1 | 26 | 3,487 | 1,235 | 4,722 | 14.0x |
| [ahujasid mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) 2.0.0 | 31 | 7,111 | 353 | 7,464 | 22.1x |

`cl100k_base` gives nearly identical numbers (330 / 4,651 / 7,393).

## What our design costs later

This server keeps operation details out of the tool list. The agent fetches them with `discover`
when it needs them, and those results enter the conversation too. Counting them:

| Discovery | Extra tokens | Running total | vs. official | vs. ahujasid |
|---|---:|---:|---:|---:|
| None (tool list only) | 0 | 338 | 14.0x less | 22.1x less |
| Operation summaries (`discover()`) | 189 | 527 | 9.0x less | 14.2x less |
| Summaries plus a typical scene's six schemas: primitive, material, assign_material, array, light, camera | 464 | 802 | 5.9x less | 9.3x less |
| Worst case: summaries plus every operation schema | 918 | 1,256 | 3.8x less | 5.9x less |

## How the definitions stay small

FastMCP generates JSON Schema from Python signatures, and that schema carries noise the model never
reads. Before listing tools, the server removes it:

| Removed | Example | Why it's safe |
|---|---|---|
| Generated titles | `"title": "Names"`, `"title": "inspectArguments"` | Names already identify each parameter. |
| `Optional[X] = None` unions | `"anyOf": [X, {"type": "null"}], "default": null` becomes `X` | Leaving the argument out already means `None`. |
| `additionalProperties: true` | on each `execute` step | It is the JSON Schema default. |
| Docstring indentation and blank lines | `"\n\n    dry_run checks..."` | Whitespace carries no meaning for the model. |

That took the four definitions from 406 to 289 tokens, even after adding capture's `engine`
argument. `tests/test_server.py` fails if they grow past 300 tokens or the noise comes back.

## Method

1. Launch each server over stdio with the official MCP Python SDK.
2. Call `initialize` and `tools/list`. No Blender instance is involved, and nothing is executed.
3. Serialize `[{name, description, inputSchema}]` as compact JSON and count tokens. Server
   `instructions` from `initialize` are counted separately.

Reproduce with [scripts/bench_tool_context.py](../scripts/bench_tool_context.py):

```sh
uv run python scripts/bench_tool_context.py servers.json --out docs/tool-context.json
```

where `servers.json` lists the commands to launch, for example:

```json
[
  {"label": "Frugal Blender MCP", "command": "uvx", "args": ["frugal-blender-mcp"]},
  {"label": "ahujasid mcp-for-blender", "command": "uvx", "args": ["mcp-for-blender"]},
  {"label": "Blender Lab official", "command": "uv", "args": ["run", "--directory", "/path/to/blender_mcp", "blender-mcp"]}
]
```

## What this does not show

- **Clients wrap definitions differently.** Exact counts vary by client and model tokenizer. The ratios
  are what matter.
- **Some clients load tools lazily.** Clients with tool search or deferred loading (for example
  Claude Code with many tools) only pay for the tools they load, which shrinks the gap. Clients that
  load every definition up front pay the full cost on every request.
- **Prompt caching lowers the price** of repeated definitions but not the context window they occupy.
- **Fewer tools are not automatically better.** The other servers offer things this one does not,
  such as documentation search (official) and asset-provider integrations (ahujasid). This benchmark
  measures one cost, not overall capability or output quality.
