"""Measure the fixed context cost of MCP servers: tool definitions plus server instructions.

Each server is launched over stdio, initialized and asked for tools/list. Nothing is sent to
Blender; no Blender instance is needed. The serialized JSON is tokenized with tiktoken.

Usage:
    uv run python scripts/bench_tool_context.py servers.json [--out docs/tool-context.json]

servers.json is a list of {"label", "command", "args", "cwd"?} objects.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

import tiktoken
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ENCODINGS = ("o200k_base", "cl100k_base")


async def list_tools(server):
    params = StdioServerParameters(
        command=server["command"], args=server.get("args", []), cwd=server.get("cwd")
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            tools = (await session.list_tools()).tools
    definitions = [
        {"name": t.name, "description": t.description, "inputSchema": t.inputSchema} for t in tools
    ]
    return init.serverInfo, init.instructions or "", definitions


def tokens(text):
    return {name: len(tiktoken.get_encoding(name).encode(text)) for name in ENCODINGS}


async def measure(server):
    info, instructions, definitions = await list_tools(server)
    schema_text = json.dumps(definitions, separators=(",", ":"), ensure_ascii=False)
    return {
        "label": server["label"],
        "server": {"name": info.name, "version": info.version},
        "tools": len(definitions),
        "tool_names": [d["name"] for d in definitions],
        "definition_tokens": tokens(schema_text),
        "instruction_tokens": tokens(instructions),
        "total_tokens": {k: tokens(schema_text)[k] + tokens(instructions)[k] for k in ENCODINGS},
    }


def table(rows):
    lines = [
        "| Server | Tools | Definition tokens | Instruction tokens | Total (o200k) |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in sorted(rows, key=lambda r: r["total_tokens"]["o200k_base"]):
        lines.append(
            f"| {r['label']} | {r['tools']} | {r['definition_tokens']['o200k_base']:,} | "
            f"{r['instruction_tokens']['o200k_base']:,} | {r['total_tokens']['o200k_base']:,} |"
        )
    return "\n".join(lines)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("servers", type=Path)
    parser.add_argument("--out", type=Path)
    ns = parser.parse_args()
    rows = []
    for server in json.loads(ns.servers.read_text(encoding="utf-8-sig")):
        try:
            rows.append(await measure(server))
        except Exception as exc:  # report and continue; one broken server should not hide the rest
            print(f"{server['label']}: failed: {exc!r}", file=sys.stderr)
    print(table(rows))
    if ns.out:
        ns.out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
