#!/usr/bin/env python3
"""Minimal stdio MCP server for HTML to LVGL migration helpers."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_SCRIPT = ROOT / "scripts" / "html_to_lvgl_inventory.py"
MAPPING_REFERENCE = ROOT / "skills" / "html-to-lvgl" / "references" / "lvgl_mapping.md"

spec = importlib.util.spec_from_file_location("html_to_lvgl_inventory", INVENTORY_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Could not load inventory helper: {INVENTORY_SCRIPT}")
inventory_mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = inventory_mod
spec.loader.exec_module(inventory_mod)


TOOLS = [
    {
        "name": "inventory_html",
        "description": "Extract a conservative HTML to LVGL migration inventory from a local HTML file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "html_file": {
                    "type": "string",
                    "description": "Path to a local HTML file. Relative paths are resolved from the current workspace.",
                },
                "format": {
                    "type": "string",
                    "description": "Output format: md or json.",
                    "default": "md",
                },
            },
            "required": ["html_file"],
        },
    },
    {
        "name": "mapping_reference",
        "description": "Return the HTML/CSS to LVGL v8 component mapping reference.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


def content_text(value: Any) -> dict[str, Any]:
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, indent=2)
    return {"content": [{"type": "text", "text": value}]}


def resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def inventory_html(html_file: str, output_format: str) -> str:
    if output_format not in {"md", "json"}:
        raise ValueError("format must be md or json")
    path = resolve_path(html_file)
    if not path.exists():
        raise FileNotFoundError(f"HTML file not found: {path}")
    inventory = inventory_mod.extract_inventory(path)
    if output_format == "json":
        return json.dumps(inventory, ensure_ascii=False, indent=2)
    return inventory_mod.emit_markdown(inventory)


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")

    if method == "notifications/initialized":
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "html-to-lvgl", "version": "0.1.0"},
            },
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        try:
            if name == "inventory_html":
                result = inventory_html(str(args["html_file"]), str(args.get("format", "md")))
                return {"jsonrpc": "2.0", "id": request_id, "result": content_text(result)}
            if name == "mapping_reference":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": content_text(MAPPING_REFERENCE.read_text(encoding="utf-8")),
                }
            raise ValueError(f"Unknown tool: {name}")
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": str(exc)}],
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            response = handle_request(json.loads(line))
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(exc)},
            }
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
