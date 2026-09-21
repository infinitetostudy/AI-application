"""Turn a Pydantic model into an OpenAI-style strict JSON Schema."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def strict_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    schema = model.model_json_schema()
    defs = schema.get("$defs") or schema.get("definitions") or {}
    for definition in defs.values():
        _strictify(definition)
    _strictify(schema)
    return schema


def _strictify(node: Any) -> None:
    if not isinstance(node, dict):
        return
    for key in ("anyOf", "oneOf", "allOf"):
        for item in node.get(key, []):
            _strictify(item)
    if "items" in node:
        _strictify(node["items"])
    if "properties" in node:
        node["type"] = "object"
        node["additionalProperties"] = False
        node["required"] = list(node["properties"].keys())
        for child in node["properties"].values():
            _strictify(child)
    if "$defs" in node:
        for definition in node["$defs"].values():
            _strictify(definition)
