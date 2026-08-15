"""Phase 2 ingestion and agent-memory preparation."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from probception.adapters.google_sheet import GoogleSheetCsvAdapter
from probception.memory import MemoryRecord, canonical_source_label, get_memory_store
from probception.types import content_id

PHASE1_SHEET_ID = "1Rz6w9t2_BOzPMBghsz8tDFhRe5AxCwayz7ablT3FVXI"
PHASE1_GID = "0"
PHASE1_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{PHASE1_SHEET_ID}/gviz/tq?"
    f"tqx=out:csv&gid={PHASE1_GID}"
)
PAPER_FETCH_SOURCES = [
    "trials/us",
    "fda",
    "pmc",
    "arxiv",
    "biorxiv",
    "medrxiv",
    "openalex",
]

DOMAIN_KEYS = [
    "disease_context_mechanism",
    "trial_design",
    "acute_safety_tolerability",
    "long_term_genetic_risk",
    "biodistribution_pharmacology",
    "immunogenicity_special_populations",
    "product_quality_cmc",
    "trial_integrity_governance_ops",
    "benefit_risk_postmarketing",
    "regulatory_precedent",
    "comparative_landscape",
    "commercial_viability",
]


class Phase1Domain(BaseModel):
    """One row from the Phase 1 regulatory review map."""

    id: str = ""
    domain_key: str
    review_domain: str
    core_question: str = ""
    primary_review_data: str = ""
    detailed_review_elements: str = ""
    source_url: str = PHASE1_CSV_URL
    row_number: int
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            object.__setattr__(
                self,
                "id",
                content_id(
                    {
                        "domain_key": self.domain_key,
                        "review_domain": self.review_domain,
                        "core_question": self.core_question,
                    },
                    "ph1",
                ),
            )

    def as_text(self) -> str:
        return "\n".join(
            part
            for part in (
                f"Domain: {self.review_domain}",
                f"Question: {self.core_question}",
                f"Primary data: {self.primary_review_data}",
                f"Detailed elements: {self.detailed_review_elements}",
            )
            if part.split(": ", 1)[-1].strip()
        )


def fetch_phase1_csv(url: str = PHASE1_CSV_URL, timeout: int = 30) -> str:
    """Fetch the public Phase 1 Google Sheet CSV."""
    return GoogleSheetCsvAdapter().fetch_csv(url, timeout=timeout)


def load_phase1_domains(csv_text: str) -> list[Phase1Domain]:
    """Parse the Phase 1 sheet with stable domain labels."""
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    domains: list[Phase1Domain] = []
    for index, row in enumerate(rows):
        review_domain = (row.get("FDA Review Domain") or "").strip()
        key = DOMAIN_KEYS[index] if index < len(DOMAIN_KEYS) else _slug(review_domain)
        domains.append(
            Phase1Domain(
                domain_key=key,
                review_domain=review_domain,
                core_question=(row.get("Core Regulatory Question") or "").strip(),
                primary_review_data=(row.get("Primary Review Data (Act 1)") or "").strip(),
                detailed_review_elements=(
                    row.get("Detailed Review Elements & Dossier Components") or ""
                ).strip(),
                row_number=index + 2,
                metadata={
                    "sheet_id": PHASE1_SHEET_ID,
                    "gid": PHASE1_GID,
                    "empty_fields": [name for name, value in row.items() if name and not value],
                },
            )
        )
    return domains


def phase1_memory_records(domains: list[Phase1Domain]) -> list[MemoryRecord]:
    """Convert Phase 1 rubric rows into compact reusable memory records."""
    records = []
    for domain in domains:
        records.append(
            MemoryRecord(
                namespace="phase2",
                kind="phase1_domain",
                source=domain.source_url,
                source_label=f"phase1:{domain.domain_key}",
                title=domain.review_domain or domain.domain_key,
                text=domain.as_text(),
                metadata=domain.model_dump(mode="json"),
            )
        )
    return records


def ingest_phase1_sheet(
    *,
    url: str = PHASE1_CSV_URL,
    data_dir: str | Path = "data",
    write_files: bool = True,
    store_memory: bool = True,
) -> dict[str, Any]:
    """Fetch, normalize, persist, and optionally memorize the Phase 1 sheet."""
    csv_text = fetch_phase1_csv(url)
    domains = load_phase1_domains(csv_text)
    records = phase1_memory_records(domains)
    memory_upserts = 0
    if store_memory:
        memory_upserts = get_memory_store().upsert_many(records)

    csv_path = Path(data_dir) / "phase1_regulatory_review_map.csv"
    json_path = Path(data_dir) / "phase1_regulatory_review_map.json"
    if write_files:
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        csv_path.write_text(csv_text, encoding="utf-8")
        json_path.write_text(
            json.dumps([d.model_dump(mode="json") for d in domains], indent=2),
            encoding="utf-8",
        )

    return {
        "source_url": url,
        "rows": len(domains),
        "domain_keys": [d.domain_key for d in domains],
        "csv_path": str(csv_path) if write_files else "",
        "json_path": str(json_path) if write_files else "",
        "memory_records": len(records),
        "memory_upserts": memory_upserts,
    }


def memory_records_from_sources(sources: list[dict[str, Any]], namespace: str = "phase2") -> list[MemoryRecord]:
    """Normalize arbitrary source documents into reusable memory records."""
    records = []
    for item in sources:
        source = str(item.get("source") or item.get("url") or item.get("id") or "unknown")
        title = str(item.get("title") or item.get("name") or item.get("asset") or "")
        text = str(item.get("text") or item.get("summary") or item.get("claim") or item)
        records.append(
            MemoryRecord(
                namespace=namespace,
                kind=str(item.get("kind") or "source_document"),
                source=source,
                source_label=canonical_source_label(source, title),
                title=title,
                text=text,
                metadata=item,
            )
        )
    return records


def build_paper_fetch_plan(
    asset: str,
    planned_trial_design: str = "",
    *,
    learned_context: list[str] | None = None,
) -> list[dict[str, str]]:
    """Create deterministic source-specific literature and trial searches."""
    base_terms = " ".join(part for part in [asset, planned_trial_design] if part).strip()
    learned_terms = " ".join(_learned_query_terms(learned_context or []))
    shared = " ".join(part for part in [base_terms, learned_terms] if part).strip()
    templates = {
        "trials/us": "{shared} clinical trial safety efficacy phase",
        "fda": "{shared} FDA review briefing document CRISPR LNP",
        "pmc": "{shared} in vivo CRISPR LNP safety efficacy",
        "arxiv": "{shared} CRISPR delivery off-target analysis",
        "biorxiv": "{shared} preclinical biodistribution immunogenicity",
        "medrxiv": "{shared} clinical outcomes adverse events",
        "openalex": "{shared} citation landscape comparator asset",
    }
    return [
        {"source": source, "query": template.format(shared=shared or asset)}
        for source, template in templates.items()
    ]


def fetch_strategy_records(
    asset: str,
    planned_trial_design: str,
    attempts: list[dict[str, Any]],
    *,
    namespace: str = "phase2",
) -> list[MemoryRecord]:
    """Persist how evidence was searched so future agents can reuse the route."""
    records = []
    for attempt in attempts:
        source = str(attempt.get("source") or "paperclip")
        query = str(attempt.get("query") or "")
        result = str(attempt.get("result") or "")[:2000]
        records.append(
            MemoryRecord(
                namespace=namespace,
                kind="fetch_strategy",
                source=f"probception:paper_fetch:{source}",
                source_label=f"fetch:{_slug(asset)}:{_slug(source)}",
                title=f"{asset} fetch strategy for {source}",
                text=(
                    f"Asset: {asset}\n"
                    f"Planned trial design: {planned_trial_design}\n"
                    f"Source: {source}\n"
                    f"Query: {query}\n"
                    f"Observed result snippet: {result}"
                ),
                metadata={
                    "asset": asset,
                    "planned_trial_design": planned_trial_design,
                    "source": source,
                    "query": query,
                },
            )
        )
    return records


def _learned_query_terms(context: list[str]) -> list[str]:
    terms: list[str] = []
    for text in context:
        lower = text.lower()
        for marker in (
            "off-target",
            "biodistribution",
            "immunogenicity",
            "dose-response",
            "adverse events",
            "ldl-c",
            "pcsk9",
            "liver",
            "lnp",
        ):
            if marker in lower and marker not in terms:
                terms.append(marker)
        if len(terms) >= 5:
            break
    return terms


def _slug(value: str) -> str:
    out = []
    previous = False
    for char in value.lower():
        if char.isalnum():
            out.append(char)
            previous = False
        elif not previous:
            out.append("_")
            previous = True
    return "".join(out).strip("_") or "domain"
