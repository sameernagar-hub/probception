"""Runtime configuration, loaded once from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=False)


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Settings:
    # Core
    mode: str = field(default_factory=lambda: _get("PROBCEPTION_MODE", "mock"))
    seed: int = field(default_factory=lambda: int(_get("PROBCEPTION_SEED", "1729") or 1729))
    run_dir: Path = field(default_factory=lambda: Path(_get("PROBCEPTION_RUN_DIR", "runs")))

    # Claude
    anthropic_api_key: str = field(default_factory=lambda: _get("ANTHROPIC_API_KEY"))
    model: str = field(default_factory=lambda: _get("PROBCEPTION_MODEL", "claude-opus-5"))
    effort: str = field(default_factory=lambda: _get("PROBCEPTION_EFFORT", "high"))

    # Partner tools
    paperclip_api_key: str = field(default_factory=lambda: _get("PAPERCLIP_API_KEY"))
    paperclip_base_url: str = field(
        default_factory=lambda: _get("PAPERCLIP_BASE_URL", "https://api.paperclip.gxl.ai")
    )
    proto_api_key: str = field(default_factory=lambda: _get("PROTO_API_KEY"))
    proto_base_url: str = field(default_factory=lambda: _get("PROTO_BASE_URL"))
    modal_token_id: str = field(default_factory=lambda: _get("MODAL_TOKEN_ID"))
    modal_token_secret: str = field(default_factory=lambda: _get("MODAL_TOKEN_SECRET"))
    tamarind_api_key: str = field(default_factory=lambda: _get("TAMARIND_API_KEY"))
    tamarind_base_url: str = field(
        default_factory=lambda: _get("TAMARIND_BASE_URL", "https://app.tamarind.bio/api")
    )
    benchling_api_key: str = field(default_factory=lambda: _get("BENCHLING_API_KEY"))
    phylo_api_key: str = field(default_factory=lambda: _get("PHYLO_API_KEY"))
    mongodb_uri: str = field(default_factory=lambda: _get("MONGODB_URI"))

    @property
    def live(self) -> bool:
        return self.mode.lower() == "live"

    @property
    def has_claude(self) -> bool:
        return bool(self.anthropic_api_key)

    def credential_report(self) -> list[tuple[str, bool, str]]:
        """(name, present, where-to-get-it) for the `probception doctor` command."""
        return [
            ("ANTHROPIC_API_KEY", bool(self.anthropic_api_key), "platform.claude.com"),
            ("PAPERCLIP_API_KEY", bool(self.paperclip_api_key), "paperclip.gxl.ai/login"),
            ("PROTO_API_KEY", bool(self.proto_api_key), "Proto credits slide"),
            ("MODAL_TOKEN_ID", bool(self.modal_token_id), "modal setup"),
            ("TAMARIND_API_KEY", bool(self.tamarind_api_key), "app.tamarind.bio"),
            ("MONGODB_URI", bool(self.mongodb_uri), "MongoDB Atlas"),
            ("BENCHLING_API_KEY", bool(self.benchling_api_key), "hackathon.bnchdev.org"),
            ("PHYLO_API_KEY", bool(self.phylo_api_key), "biomni.phylo.bio"),
        ]


settings = Settings()
