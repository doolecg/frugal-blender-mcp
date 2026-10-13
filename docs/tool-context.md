# Fixed context cost of Blender MCP servers

Every MCP client sends the server's tool definitions (and any server instructions) to the model
before the first prompt, and again on every request after that. That cost is paid even when the
agent never touches Blender. This benchmark measures it.

Measured on 2026-10-13, Windows 11, tokenized with tiktoken. Raw output: [tool-context.json](tool-context.json).

| Server | Tools | Definition tokens | Instruction tokens | Total (o200k) | vs. this repo |
|---|---:|---:|---:|---:|---:|
| **Blender Astra MCP** (this repo, 0.2.0) | **4** | 352 | 49 | **401** | 1x |
| [Blender Lab official](https://projects.blender.org/lab/blender_mcp) blender-mcp 1.0.1 | 26 | 3,487 | 1,235 | 4,722 | 11.8x |
| [ahujasid mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) 2.0.0 | 31 | 7,111 | 353 | 7,464 | 18.6x |

`cl100k_base` gives nearly identical numbers (393 / 4,651 / 7,393).

## What our design costs later

This server keeps operation details out of the tool list. The agent fetches them with `discover`
when it needs them, and those results enter the conversation too. Counting them:

| Discovery | Extra tokens | Running total | vs. official | vs. ahujasid |
|---|---:|---:|---:|---:|
| None (tool list only) | 0 | 401 | 11.8x less | 18.6x less |
| Operation summaries (`discover()`) | 189 | 590 | 8.0x less | 12.7x less |
| Summaries plus a typical scene's six schemas: primitive, material, assign_material, array, light, camera | 464 | 865 | 5.5x less | 8.6x less |
| Worst case: summaries plus every operation schema | 918 | 1,319 | 3.6x less | 5.7x less |

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
  {"label": "Blender Astra MCP", "command": "uvx", "args": ["blender-astra-mcp"]},
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
