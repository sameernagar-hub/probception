"""Claude client wrapper: structured outputs, prompt caching, and full tracing.

Two rules this module enforces for the rest of the codebase:

1.  Every model call is logged to the ledger with its prompt hash, token usage
    and latency, so the cost and provenance of a conclusion are inspectable.
2.  Every model call returns a *typed* object, never free text. If Claude cannot
    fill the schema, we find out at the boundary rather than three layers later.

Model defaults follow the Claude Opus 5 guidance: thinking is on by default,
`effort` controls depth, and the stable system prompt carries a cache breakpoint
so repeated calls in a loop read the prefix at ~0.1x input cost.
"""

from __future__ import annotations

import time
from typing import Any, TypeVar

from pydantic import BaseModel

from probception.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMUnavailable(RuntimeError):
    """No API key, or the anthropic package is not installed."""


class Claude:
    """Thin, traced wrapper around the Anthropic Messages API."""

    def __init__(
        self,
        model: str | None = None,
        effort: str | None = None,
        ledger: Any | None = None,
    ):
        self.model = model or settings.model
        self.effort = effort or settings.effort
        self.ledger = ledger
        self._client = None

    # -- lifecycle -------------------------------------------------------
    @property
    def available(self) -> bool:
        if not settings.has_claude:
            return False
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        return True

    def _ensure(self):
        if self._client is not None:
            return self._client
        if not settings.has_claude:
            raise LLMUnavailable(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key, "
                "or run with PROBCEPTION_MODE=mock to use the offline reasoner."
            )
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - install-time failure
            raise LLMUnavailable("pip install anthropic") from exc
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    # -- calls -----------------------------------------------------------
    def structured(
        self,
        *,
        system: str,
        user: str,
        schema: type[T],
        max_tokens: int = 16000,
        label: str = "structured",
    ) -> T:
        """Ask Claude for one object of type `schema`. Raises if it cannot comply."""
        client = self._ensure()
        started = time.perf_counter()

        # The system prompt is the stable prefix across every step of a run, so
        # it carries the cache breakpoint. Volatile per-step content goes in the
        # user turn, after the breakpoint, where it cannot invalidate the cache.
        system_blocks = [
            {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
        ]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_blocks,
            "messages": [{"role": "user", "content": user}],
            "output_format": schema,
        }

        try:
            response = client.messages.parse(
                **kwargs, output_config={"effort": self.effort}
            )
        except TypeError:
            # Older SDKs do not accept output_config alongside output_format.
            response = client.messages.parse(**kwargs)

        elapsed = time.perf_counter() - started
        parsed = response.parsed_output
        if parsed is None:
            raise LLMUnavailable(
                f"Claude returned no parseable {schema.__name__} "
                f"(stop_reason={response.stop_reason})."
            )

        self._trace(label, system, user, response, elapsed)
        return parsed

    def _trace(self, label: str, system: str, user: str, response: Any, elapsed: float) -> None:
        if self.ledger is None:
            return
        usage = getattr(response, "usage", None)
        self.ledger.append(
            "model_call",
            {
                "label": label,
                "model": self.model,
                "effort": self.effort,
                "stop_reason": getattr(response, "stop_reason", None),
                "latency_s": round(elapsed, 3),
                "system_chars": len(system),
                "user_chars": len(user),
                "usage": {
                    "input_tokens": getattr(usage, "input_tokens", None),
                    "output_tokens": getattr(usage, "output_tokens", None),
                    "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", None),
                    "cache_creation_input_tokens": getattr(
                        usage, "cache_creation_input_tokens", None
                    ),
                },
            },
            note=f"Claude call: {label}",
        )
