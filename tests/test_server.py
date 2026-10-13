import asyncio
import json

import tiktoken

from compact_mcp import server


def definitions():
    tools = asyncio.run(server.mcp.list_tools())
    return [{"name": t.name, "description": t.description, "inputSchema": t.inputSchema} for t in tools]


def test_tool_definitions_stay_lean():
    text = json.dumps(definitions(), separators=(",", ":"))
    assert [d["name"] for d in definitions()] == ["inspect", "discover", "execute", "capture"]
    assert '"title"' not in text and "null" not in text and "\\n" not in text
    # Fixed context is the product: every client pays it on every request.
    assert len(tiktoken.get_encoding("o200k_base").encode(text)) <= 300


def test_lean_collapses_optional_and_keeps_parameters_named_title():
    schema = {
        "title": "fnArguments",
        "type": "object",
        "properties": {
            "title": {"title": "Title", "type": "string"},
            "names": {
                "anyOf": [{"items": {"type": "string"}, "type": "array"}, {"type": "null"}],
                "default": None,
            },
            "steps": {"items": {"additionalProperties": True, "type": "object"}, "type": "array"},
        },
        "required": ["title"],
    }
    assert server.lean(schema) == {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "names": {"items": {"type": "string"}, "type": "array"},
            "steps": {"items": {"type": "object"}, "type": "array"},
        },
        "required": ["title"],
    }
