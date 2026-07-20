from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Protocol


class CompressionError(RuntimeError):
    pass


class CompressionAdapter(Protocol):
    def compress(self, payload: str, target_tokens: int) -> str: ...


@dataclass
class ConservativeCompressor:
    chars_per_token: int = 4

    def compress(self, payload: str, target_tokens: int) -> str:
        return payload[: max(target_tokens * self.chars_per_token, 0)]


@dataclass
class HeadroomCompressor:
    command: str = "headroom"
    timeout_seconds: int = 30

    def compress(self, payload: str, target_tokens: int) -> str:
        executable = shutil.which(self.command)
        if executable is None:
            raise CompressionError("Headroom executable not found")
        request = json.dumps({"text": payload, "target_tokens": target_tokens})
        proc = subprocess.run(
            [executable, "compress", "--json"],
            input=request,
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if proc.returncode != 0:
            raise CompressionError(proc.stderr.strip() or "Headroom compression failed")
        try:
            response = json.loads(proc.stdout)
            compressed = response["text"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise CompressionError("invalid Headroom response") from exc
        if not isinstance(compressed, str):
            raise CompressionError("Headroom response text must be a string")
        return compressed


@dataclass
class ASTAwareCompressor:
    """Keeps structural declarations and removes low-value blank/comment lines.

    This adapter is intentionally language-neutral for the pilot. Platform-specific
    tree-sitter adapters can replace it without changing the Guardian contract.
    """

    chars_per_token: int = 4

    def compress(self, payload: str, target_tokens: int) -> str:
        limit = max(target_tokens * self.chars_per_token, 0)
        lines = payload.splitlines()
        structural = []
        secondary = []
        markers = ("class ", "def ", "function ", "procedure ", "CREATE ", "TABLE ", "SELECT ")
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "//", "--")):
                continue
            (structural if any(marker in line for marker in markers) else secondary).append(line)
        result = "\n".join(structural + secondary)
        return result[:limit]


@dataclass
class FallbackCompressor:
    primary: CompressionAdapter
    fallback: CompressionAdapter

    def compress(self, payload: str, target_tokens: int) -> str:
        try:
            return self.primary.compress(payload, target_tokens)
        except CompressionError:
            return self.fallback.compress(payload, target_tokens)

    def __call__(self, payload: str, target_tokens: int) -> str:
        return self.compress(payload, target_tokens)
