"""Persistent memory for Phase 2 agent orchestration.

Memory is a cache and retrieval layer, not an inference layer. It stores source
documents, sheet rows, labels, and prior retrieval results so agents can avoid
refetching and reprompting the same material. It never scores experiments and it
never updates beliefs.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from probception.types import content_id

_WORD_RE = re.compile(r"[a-z0-9]+")
_DEFAULT_DIMS = 64


class MemoryRecord(BaseModel):
    """One reusable item in agent memory."""

    id: str = ""
    namespace: str = "phase2"
    kind: str
    source: str
    source_label: str
    title: str = ""
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def model_post_init(self, __context: Any) -> None:
        if not self.embedding:
            object.__setattr__(self, "embedding", deterministic_embedding(self.search_text()))
        if not self.id:
            object.__setattr__(
                self,
                "id",
                content_id(
                    {
                        "namespace": self.namespace,
                        "kind": self.kind,
                        "source_label": self.source_label,
                        "title": self.title,
                        "text": self.text[:1000],
                    },
                    "mem",
                ),
            )

    def search_text(self) -> str:
        return " ".join([self.title, self.source_label, self.text])


class MemoryStore(Protocol):
    """Small surface shared by Atlas and local fallback stores."""

    def upsert_many(self, records: list[MemoryRecord]) -> int: ...

    def search(self, query: str, *, namespace: str = "phase2", limit: int = 8) -> list[MemoryRecord]: ...


class LocalMemoryStore:
    """JSONL fallback memory that works without Atlas or network."""

    def __init__(self, path: str | Path = ".probception_memory/memory.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def upsert_many(self, records: list[MemoryRecord]) -> int:
        existing = {record.id: record for record in self._read_all()}
        changed = 0
        for record in records:
            if existing.get(record.id) != record:
                existing[record.id] = record
                changed += 1
        self.path.write_text(
            "\n".join(r.model_dump_json() for r in existing.values()) + ("\n" if existing else ""),
            encoding="utf-8",
        )
        return changed

    def search(self, query: str, *, namespace: str = "phase2", limit: int = 8) -> list[MemoryRecord]:
        query_embedding = deterministic_embedding(query)
        rows = [r for r in self._read_all() if r.namespace == namespace]
        scored = [
            (_cosine(query_embedding, record.embedding), record)
            for record in rows
            if _has_overlap(query, record.search_text())
        ]
        if not scored:
            scored = [(_cosine(query_embedding, record.embedding), record) for record in rows]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [record for _, record in scored[:limit]]

    def _read_all(self) -> list[MemoryRecord]:
        if not self.path.exists():
            return []
        records = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(MemoryRecord.model_validate_json(line))
        return records


class AtlasMemoryStore:
    """MongoDB Atlas-backed memory store with vector-search fallback paths."""

    def __init__(
        self,
        uri: str,
        *,
        database: str = "probception",
        collection: str = "agent_memory",
        timeout_ms: int = 5000,
    ):
        try:
            from pymongo import MongoClient, ReplaceOne  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Install the optional memory extra: uv sync --extra memory") from exc

        self._replace_one = ReplaceOne
        self.client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)
        self.collection = self.client[database][collection]
        self.collection.create_index("id", unique=True)
        self.collection.create_index([("namespace", 1), ("source_label", 1), ("kind", 1)])
        self.collection.create_index([("text", "text"), ("title", "text"), ("source_label", "text")])

    def upsert_many(self, records: list[MemoryRecord]) -> int:
        if not records:
            return 0
        operations = [
            self._replace_one({"id": record.id}, record.model_dump(mode="json"), upsert=True)
            for record in records
        ]
        result = self.collection.bulk_write(operations, ordered=False)
        return int(result.upserted_count + result.modified_count)

    def search(self, query: str, *, namespace: str = "phase2", limit: int = 8) -> list[MemoryRecord]:
        vector_results = self._vector_search(query, namespace=namespace, limit=limit)
        if vector_results:
            return vector_results
        text_results = self._text_search(query, namespace=namespace, limit=limit)
        if text_results:
            return text_results
        docs = self.collection.find({"namespace": namespace}).limit(limit)
        return [MemoryRecord.model_validate(doc) for doc in docs]

    def _vector_search(self, query: str, *, namespace: str, limit: int) -> list[MemoryRecord]:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "agent_memory_embedding",
                    "path": "embedding",
                    "queryVector": deterministic_embedding(query),
                    "numCandidates": max(limit * 8, 32),
                    "limit": limit,
                    "filter": {"namespace": namespace},
                }
            }
        ]
        try:
            return [MemoryRecord.model_validate(doc) for doc in self.collection.aggregate(pipeline)]
        except Exception:
            return []

    def _text_search(self, query: str, *, namespace: str, limit: int) -> list[MemoryRecord]:
        try:
            docs = self.collection.find(
                {"namespace": namespace, "$text": {"$search": query}},
                {"score": {"$meta": "textScore"}},
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            return [MemoryRecord.model_validate(doc) for doc in docs]
        except Exception:
            return []


def get_memory_store() -> MemoryStore:
    """Resolve Atlas memory when configured, otherwise local deterministic memory."""
    load_secret_env()
    uri = os.environ.get("MONGODB_URI", "").strip()
    if uri:
        try:
            return AtlasMemoryStore(
                uri,
                database=os.environ.get("PROBCEPTION_MEMORY_DB", "probception"),
                collection=os.environ.get("PROBCEPTION_MEMORY_COLLECTION", "agent_memory"),
            )
        except Exception:
            pass
    return LocalMemoryStore(os.environ.get("PROBCEPTION_LOCAL_MEMORY", ".probception_memory/memory.jsonl"))


def load_secret_env() -> None:
    """Load local secret files without requiring them to live in the repo."""
    load_dotenv(override=False)
    explicit = os.environ.get("PROBCEPTION_ATLAS_ENV_PATH")
    candidates = [
        Path(explicit) if explicit else None,
        Path("atlas-credentials.env"),
        Path("../atlas-credentials.env"),
        Path.home() / "Downloads" / "atlas-credentials.env",
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            load_dotenv(candidate, override=False)


def canonical_source_label(source: str, title: str = "") -> str:
    """Collapse similar source strings so prompts can cite one compact label."""
    text = f"{source} {title}".lower()
    if "clinicaltrials.gov" in text or re.search(r"\bnct\d{8}\b", text):
        nct = re.search(r"\b(nct\d{8})\b", text)
        return f"ctgov:{nct.group(1).upper()}" if nct else "ctgov:trial"
    if "paperclip.gxl.ai/citations/fda/" in text:
        match = re.search(r"fda_[a-z0-9]+", text)
        return f"fda:{match.group(0)}" if match else "fda:paperclip"
    if "fda" in text:
        return "fda:review"
    if "pubmed" in text or "pmc" in text:
        return "pmc:article"
    if "biorxiv" in text:
        return "biorxiv:preprint"
    if "medrxiv" in text:
        return "medrxiv:preprint"
    if "uniprot" in text:
        return "uniprot:record"
    if "pdb" in text:
        return "pdb:structure"
    if "chembl" in text:
        return "chembl:record"
    digest = hashlib.sha1(text.encode()).hexdigest()[:10]
    slug = "-".join(_WORD_RE.findall(title.lower())[:4]) or "source"
    return f"{slug}:{digest}"


def deterministic_embedding(text: str, dims: int = _DEFAULT_DIMS) -> list[float]:
    """A tiny hashing embedding for fallback vector-like search.

    It is not semantic like a model embedding, but it is deterministic, cheap,
    and good enough to avoid reusing totally unrelated cache entries.
    """
    vector = [0.0] * dims
    for token in _WORD_RE.findall(text.lower()):
        digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dims
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [round(v / norm, 6) for v in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))


def _has_overlap(query: str, text: str) -> bool:
    q = set(_WORD_RE.findall(query.lower()))
    t = set(_WORD_RE.findall(text.lower()))
    return bool(q & t)
