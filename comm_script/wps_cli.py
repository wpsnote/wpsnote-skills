#!/usr/bin/env python3
"""Shared wpsnote-cli adapter for Python scripts across skills."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from typing import Optional


def unwrap_cli_result(raw_obj: dict, returncode: int) -> dict:
    """Normalize wpsnote-cli output (CallToolResult or legacy JSON) to {ok, data, message?}."""
    if not isinstance(raw_obj, dict):
        return {"ok": False, "message": "invalid json"}
    if "ok" in raw_obj:
        return raw_obj
    is_err = bool(raw_obj.get("isError")) or returncode != 0
    payload = raw_obj.get("structuredContent")
    if payload is None and isinstance(raw_obj.get("content"), list):
        for item in raw_obj["content"]:
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                try:
                    payload = json.loads(item["text"])
                    break
                except Exception:
                    payload = {"message": item["text"]}
    if is_err:
        msg = payload.get("message") if isinstance(payload, dict) else str(payload or "tool failed")
        return {"ok": False, "message": msg, "data": payload if isinstance(payload, dict) else {}}
    return {"ok": True, "data": payload if isinstance(payload, dict) else raw_obj}


def cli_available() -> bool:
    """Return True if wpsnote-cli is present on PATH."""
    return shutil.which("wpsnote-cli") is not None


def cli(args: list[str], timeout: int = 60) -> dict:
    """Execute wpsnote-cli with --no-update-notice --json using bytes stdout decoding."""
    cmd = ["wpsnote-cli", "--no-update-notice", *args, "--json"]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "message": str(exc)}

    raw = result.stdout.decode("utf-8", errors="ignore").strip()
    if not raw:
        err = result.stderr.decode("utf-8", errors="ignore").strip()
        return {"ok": False, "message": err or "empty"}
    try:
        idx = raw.find("{")
        return unwrap_cli_result(json.loads(raw[idx:] if idx >= 0 else raw), result.returncode)
    except Exception:
        return {"ok": False, "message": raw[:200]}


def cli_retry(args: list[str], retries: int = 3, sleep: float = 2.0) -> dict:
    """Run CLI command with retry; stop early on Block/note not found errors."""
    res: dict = {}
    for i in range(retries):
        res = cli(args)
        if res.get("ok") is not False:
            return res
        msg = res.get("message", "")
        if "Block not found" in msg or "not found" in msg.lower():
            break
        if i < retries - 1:
            time.sleep(sleep)
    return res


def cli_check(timeout: int = 10) -> bool:
    """Check whether wpsnote-cli cloud authentication is valid."""
    try:
        result = subprocess.run(
            ["wpsnote-cli", "--no-update-notice", "auth", "status", "--json"],
            capture_output=True,
            timeout=timeout,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def cli_find_note_by_title(title: str) -> Optional[str]:
    """Find a note by exact title via keyword listing and return note_id or None."""
    r = cli(["list", "--keyword", title[:40], "--limit", "20"])
    data = r.get("data") or {}
    notes = data.get("notes") or data.get("items") or []
    return next((n.get("note_id") for n in notes if n.get("title") == title), None)


def cli_create_note(title: str) -> Optional[str]:
    """Create a blank note and return note_id."""
    r = cli(["create", "--title", title])
    return (r.get("data") or {}).get("note_id") or (r.get("data") or {}).get("fileId")


def cli_sync(note_id: str) -> None:
    """Cloud writes persist immediately; kept as a compatibility no-op."""
    _ = note_id
    time.sleep(0.5)


def cli_get_outline(note_id: str) -> dict:
    """Fetch first page of note outline (up to 100 blocks)."""
    r = cli(["outline", "--note_id", note_id])
    return r.get("data") or {}


def cli_get_all_blocks(note_id: str) -> list:
    """Paginate through outline + read-blocks to retrieve every top-level block."""
    data = cli_get_outline(note_id)
    total = data.get("block_count", 0)
    blocks = list(data.get("blocks", []))
    last_id = blocks[-1]["id"] if blocks else None
    fetched = len(blocks)

    while fetched < total and last_id:
        r2 = cli(
            [
                "read-blocks",
                "--note_id",
                note_id,
                "--block_id",
                last_id,
                "--after",
                "100",
                "--include_anchor",
                "false",
            ]
        )
        new_blocks = (r2.get("data") or {}).get("blocks", [])
        if not new_blocks:
            break
        blocks.extend(new_blocks)
        last_id = new_blocks[-1]["id"]
        fetched += len(new_blocks)

    return blocks


def cli_get_last_block_id(note_id: str) -> str:
    """Return the last top-level block ID for insertion anchoring."""
    data = cli_get_outline(note_id)
    blocks = data.get("blocks", [])
    return blocks[-1]["id"] if blocks else ""


def cli_batch_edit(note_id: str, ops: list) -> dict:
    """Apply batch_edit operations with retry."""
    return cli_retry(["batch-edit", "--note_id", note_id, "--operations", json.dumps(ops)])
