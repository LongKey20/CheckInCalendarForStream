from __future__ import annotations

import csv
import os
import subprocess

from .constants import STREAMING_TOOL_PROCESSES


def detect_running_streaming_tools() -> list[str]:
    if os.name != "nt":
        return []
    try:
        result = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    found: list[str] = []
    for row in csv.reader(result.stdout.splitlines()):
        if not row:
            continue
        process_name = row[0].strip().casefold()
        tool_name = STREAMING_TOOL_PROCESSES.get(process_name)
        if tool_name and tool_name not in found:
            found.append(tool_name)
    return found
