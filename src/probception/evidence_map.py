"""Typed, citation-backed evidence maps for early therapy development.

The models deliberately record evidence provenance and uncertainty without
scoring it. Experiment ranking remains in the deterministic design layer.
"""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class EvidenceAxis(StrEnum):
    """The evidence dimensions used to evaluate a therapy program."""

    PRODUCT_CONTEXT = "product_and_treatment_context"
    CLINICAL_BENEFIT = "clinical_benefit_and_endpoint_validity"
    ACUTE_SAFETY = "acute_clinical_safety"
    LONG_TERM_SAFETY = "long_term_genetic_and_cellular_safety"
    BIODISTRIBUTION = "biodistribution_pharmacology_and_immunogenicity"
    CMC = "cmc_product_quality_and_manufacturing_comparability"
    STATISTICAL_CREDIBILITY = "statistical_credibility_and_evidence_limitations"
    RESIDUAL_UNCERTAINTY = "residual_uncertainty_and_development_action"


class EvidenceSource(StrEnum):
    """Paperclip buckets searched for candidate and analogue evidence."""

    CLIPBOARD = "clipboard"
    LITERATURE = "literature"
    TRIALS = "trials"
    REGULATORY = "regulatory"


class SourceAvailability(StrEnum):
    """Whether a source bucket was available to the retrieval workflow."""

    AVAILABLE = "available"
    NOT_PROVIDED = "not_provided"


class EvidenceMaturity(StrEnum):
    """How directly an item applies to the candidate under evaluation."""

    DIRECT = "direct"
    ANALOG = "analog"
    INFERRED = "inferred"


class SourceSearch(BaseModel):
    """One recorded Paperclip source-bucket search."""

    source: EvidenceSource
    query: str
    availability: SourceAvailability
    documents_found: int = Field(ge=0)
    note: str = ""

    @model_validator(mode="after")
    def _unavailable_sources_have_no_results(self) -> SourceSearch:
        if self.availability is SourceAvailability.NOT_PROVIDED and self.documents_found:
            raise ValueError("A source that was not provided cannot have retrieved documents.")
        return self


class EvidenceItem(BaseModel):
    """An atomic claim with a Paperclip line-pinned citation."""

    source: EvidenceSource
    maturity: EvidenceMaturity
    claim: str
    source_title: str = Field(min_length=1)
    supporting_text: str = Field(min_length=1)
    citation_url: str
    limitation: str

    @model_validator(mode="after")
    def _citation_is_paperclip_line_pinned(self) -> EvidenceItem:
        prefix = "https://paperclip.gxl.ai/citations/"
        if not self.citation_url.startswith(prefix) or "#L" not in self.citation_url:
            raise ValueError("Evidence citations must be line-pinned Paperclip URLs.")
        return self


class AxisAssessment(BaseModel):
    """Evidence and remaining uncertainty for one regulatory evidence axis."""

    axis: EvidenceAxis
    evidence: list[EvidenceItem] = Field(min_length=1)
    known: list[str] = Field(min_length=1)
    unknowns: list[str] = Field(min_length=1)
    development_actions: list[str] = Field(min_length=1)


class CandidateEvidenceMap(BaseModel):
    """A complete, non-scored evidence map for one therapy candidate."""

    product: str
    development_stage: str
    source_searches: list[SourceSearch]
    axes: list[AxisAssessment]

    @model_validator(mode="after")
    def _requires_complete_axis_and_source_coverage(self) -> CandidateEvidenceMap:
        axes = [assessment.axis for assessment in self.axes]
        sources = [search.source for search in self.source_searches]
        if len(axes) != len(set(axes)) or set(axes) != set(EvidenceAxis):
            raise ValueError("An evidence map must contain every evidence axis exactly once.")
        if len(sources) != len(set(sources)) or set(sources) != set(EvidenceSource):
            raise ValueError("An evidence map must record every Paperclip source bucket exactly once.")
        unavailable = {
            search.source
            for search in self.source_searches
            if search.availability is SourceAvailability.NOT_PROVIDED
        }
        if any(item.source in unavailable for assessment in self.axes for item in assessment.evidence):
            raise ValueError("Evidence cannot be attributed to an unavailable source bucket.")
        return self


def render_evidence_map(evidence_map: CandidateEvidenceMap) -> str:
    """Render an evidence map with the source text supporting each claim."""
    lines = [
        f"# Evidence map: {evidence_map.product}",
        "",
        f"Development stage: {evidence_map.development_stage}",
        "",
        "## Source search coverage",
        "",
        "| Source | Availability | Documents | Query / note |",
        "| --- | --- | ---: | --- |",
    ]
    for search in evidence_map.source_searches:
        detail = search.note or search.query
        lines.append(
            f"| {search.source.value} | {search.availability.value} | "
            f"{search.documents_found} | {detail} |"
        )

    for assessment in evidence_map.axes:
        heading = assessment.axis.value.replace("_", " ").title()
        lines.extend(["", f"## {heading}", "", "### Evidence"])
        for item in assessment.evidence:
            lines.extend(
                [
                    "",
                    f"- **{item.maturity.value.title()} · {item.source.value} · {item.source_title}**",
                    f"  - Claim: {item.claim}",
                    f"  - Supporting text: \"{item.supporting_text}\" "
                    f"([source]({item.citation_url}))",
                    f"  - Limitation: {item.limitation}",
                ]
            )
        lines.extend(
            [
                "",
                f"**Known:** {'; '.join(assessment.known)}",
                "",
                f"**Unresolved:** {'; '.join(assessment.unknowns)}",
                "",
                f"**Next action:** {'; '.join(assessment.development_actions)}",
            ]
        )
    return "\n".join(lines) + "\n"


def write_evidence_map(
    evidence_map: CandidateEvidenceMap, root: str | Path = "runs"
) -> tuple[Path, Path]:
    """Persist a rendered evidence map and its structured source data."""
    output_root = Path(root)
    output_root.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", evidence_map.product.split("(", maxsplit=1)[0].lower()).strip("-")
    markdown_path = output_root / f"{slug}-evidence-map.md"
    json_path = output_root / f"{slug}-evidence-map.json"
    markdown_path.write_text(render_evidence_map(evidence_map), encoding="utf-8", newline="\n")
    json_path.write_text(evidence_map.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    return markdown_path, json_path


_FDA_PRODUCT = "https://paperclip.gxl.ai/citations/fda/fda_9299bff400a7#L10-L12"
_FDA_EFFICACY = "https://paperclip.gxl.ai/citations/fda/fda_9299bff400a7#L95-L102"
_FDA_LONG_TERM_SAFETY = "https://paperclip.gxl.ai/citations/fda/fda_9299bff400a7#L13-L14"
_FDA_CMC = "https://paperclip.gxl.ai/citations/fda/fda_9299bff400a7#L23-L42"
_FDA_LABEL = "https://paperclip.gxl.ai/citations/fda/fda_3efe332e663a#L116-L120"
_FDA_CLINICAL_PHARMACOLOGY = "https://paperclip.gxl.ai/citations/fda/fda_9299bff400a7#L91-L92"
_TRIAL_STUDY_121 = "https://paperclip.gxl.ai/citations/trials/tri_94bcf74552cd#L100"
_LITERATURE_ASSESSMENT = "https://paperclip.gxl.ai/citations/papers/PMC11352399#L68-L85"


def casgevy_smoke_map() -> CandidateEvidenceMap:
    """Return a small, reproducible map proving the schema can capture CASGEVY.

    This fixture deliberately has no Clipboard evidence: no private CASGEVY
    assets were supplied. It demonstrates that source absence is explicit rather
    than substituted with public regulatory material.
    """
    return CandidateEvidenceMap(
        product="CASGEVY (exagamglogene autotemcel)",
        development_stage="approved analogue smoke fixture",
        source_searches=[
            SourceSearch(
                source=EvidenceSource.CLIPBOARD,
                query="CASGEVY private candidate assets",
                availability=SourceAvailability.NOT_PROVIDED,
                documents_found=0,
                note="No private candidate assets were supplied to this smoke test.",
            ),
            SourceSearch(
                source=EvidenceSource.LITERATURE,
                query="exagamglogene autotemcel transfusion independence",
                availability=SourceAvailability.AVAILABLE,
                documents_found=5,
            ),
            SourceSearch(
                source=EvidenceSource.TRIALS,
                query="NCT03745287",
                availability=SourceAvailability.AVAILABLE,
                documents_found=2,
            ),
            SourceSearch(
                source=EvidenceSource.REGULATORY,
                query="CASGEVY",
                availability=SourceAvailability.AVAILABLE,
                documents_found=8,
            ),
        ],
        axes=[
            AxisAssessment(
                axis=EvidenceAxis.PRODUCT_CONTEXT,
                evidence=[
                    EvidenceItem(
                        source=EvidenceSource.REGULATORY,
                        maturity=EvidenceMaturity.DIRECT,
                        claim=(
                            "CASGEVY is an autologous CD34+ HSPC product edited ex vivo with "
                            "CRISPR/Cas9 and infused after myeloablative conditioning."
                        ),
                        source_title="FDA Summary Basis for Regulatory Action: CASGEVY",
                        supporting_text=(
                            "CASGEVY is an autologous, hematopoietic, stem cell-based gene therapy."
                        ),
                        citation_url=_FDA_PRODUCT,
                        limitation="This approved-product description is not a substitute for a new candidate's CMC package.",
                    )
                ],
                known=["The product is a one-time, ex vivo autologous genome-edited cell therapy."],
                unknowns=["Applicability to an early-stage candidate with a different delivery system."],
                development_actions=["Capture target, cell type, editing reagents, and route in the candidate profile."],
            ),
            AxisAssessment(
                axis=EvidenceAxis.CLINICAL_BENEFIT,
                evidence=[
                    EvidenceItem(
                        source=EvidenceSource.REGULATORY,
                        maturity=EvidenceMaturity.DIRECT,
                        claim=(
                            "The primary efficacy outcome in Study 121 was absence of severe "
                            "vaso-occlusive crises for at least 12 consecutive months."
                        ),
                        source_title="FDA Summary Basis for Regulatory Action: CASGEVY",
                        supporting_text="29 (93.5%) were VF12 responders.",
                        citation_url=_FDA_EFFICACY,
                        limitation="The registration evidence was from a single-arm Phase 1/2/3 study.",
                    ),
                    EvidenceItem(
                        source=EvidenceSource.LITERATURE,
                        maturity=EvidenceMaturity.DIRECT,
                        claim="Published assessment describes the pivotal studies as single-arm and open-label.",
                        source_title="Regulatory Assessment of Casgevy",
                        supporting_text="both studies were single-arm, open-label studies",
                        citation_url=_LITERATURE_ASSESSMENT,
                        limitation="This source assesses the public program rather than replacing the underlying clinical dataset.",
                    ),
                ],
                known=["The clinical benefit endpoint was a durable, clinically meaningful event-free response."],
                unknowns=["Durability beyond the observed follow-up window."],
                development_actions=["Specify the candidate's next-stage endpoint and natural-history benchmark."],
            ),
            AxisAssessment(
                axis=EvidenceAxis.ACUTE_SAFETY,
                evidence=[
                    EvidenceItem(
                        source=EvidenceSource.REGULATORY,
                        maturity=EvidenceMaturity.DIRECT,
                        claim=(
                            "The prescribing information highlights neutrophil engraftment failure and "
                            "delayed platelet recovery among the treatment risks."
                        ),
                        source_title="CASGEVY Prescribing Information",
                        supporting_text="Delayed platelet engraftment has been observed with CASGEVY treatment.",
                        citation_url=_FDA_LABEL,
                        limitation="Some acute risk is attributable to conditioning and transplantation rather than editing alone.",
                    )
                ],
                known=["Acute safety monitoring must distinguish product-related and conditioning-related events."],
                unknowns=["Risk in broader populations and with longer observation."],
                development_actions=["Define attribution rules and prespecified acute-safety monitoring windows."],
            ),
            AxisAssessment(
                axis=EvidenceAxis.LONG_TERM_SAFETY,
                evidence=[
                    EvidenceItem(
                        source=EvidenceSource.REGULATORY,
                        maturity=EvidenceMaturity.DIRECT,
                        claim=(
                            "FDA identified off-target editing as the major product risk and required "
                            "postmarketing study of off-target and long-term malignancy risk."
                        ),
                        source_title="FDA Summary Basis for Regulatory Action: CASGEVY",
                        supporting_text="The major risk of treatment with CASGEVY is the potential for off-target, unintended genome editing.",
                        citation_url=_FDA_LONG_TERM_SAFETY,
                        limitation="Rare delayed risks cannot be bounded by the registration exposure alone.",
                    )
                ],
                known=["Long-term genetic safety was unresolved at approval."],
                unknowns=["The incidence of rare off-target or malignancy outcomes over long-term follow-up."],
                development_actions=["Plan prospective long-term follow-up and assay coverage for genetic risks."],
            ),
            AxisAssessment(
                axis=EvidenceAxis.BIODISTRIBUTION,
                evidence=[
                    EvidenceItem(
                        source=EvidenceSource.REGULATORY,
                        maturity=EvidenceMaturity.DIRECT,
                        claim=(
                            "Clinical pharmacology linked allelic editing and gamma-globin induction to "
                            "persistence of genome-edited cells."
                        ),
                        source_title="FDA Summary Basis for Regulatory Action: CASGEVY",
                        supporting_text="appear to correlate with in vivo persistence of genome edited cells",
                        citation_url=_FDA_CLINICAL_PHARMACOLOGY,
                        limitation="Ex vivo cell therapy biodistribution is not directly analogous to systemic vector delivery.",
                    )
                ],
                known=["Allelic editing and gamma-globin induction were used as persistence measures."],
                unknowns=["How another modality's distribution, persistence, and immune response would compare."],
                development_actions=["Match the biodistribution plan to the candidate's route and delivery platform."],
            ),
            AxisAssessment(
                axis=EvidenceAxis.CMC,
                evidence=[
                    EvidenceItem(
                        source=EvidenceSource.REGULATORY,
                        maturity=EvidenceMaturity.DIRECT,
                        claim=(
                            "The CMC review evaluated control strategy, lot release, comparability, chain of "
                            "identity/custody, shipping validation, and hold-time stability."
                        ),
                        source_title="FDA Summary Basis for Regulatory Action: CASGEVY",
                        supporting_text="traceability through chain of identity and chain of custody (COI/COC)",
                        citation_url=_FDA_CMC,
                        limitation="The manufacturing controls are product-specific and cannot establish comparability for another process.",
                    )
                ],
                known=["Manufacturing quality and comparability are integral to clinical evidence."],
                unknowns=["Whether future process changes preserve a new candidate's critical quality attributes."],
                development_actions=["Define critical quality attributes and comparability triggers before scale-up."],
            ),
            AxisAssessment(
                axis=EvidenceAxis.STATISTICAL_CREDIBILITY,
                evidence=[
                    EvidenceItem(
                        source=EvidenceSource.TRIALS,
                        maturity=EvidenceMaturity.DIRECT,
                        claim=(
                            "Study 121 was registered as a single-arm, open-label, multi-site, single-dose "
                            "Phase 1/2/3 study in severe sickle cell disease."
                        ),
                        source_title="ClinicalTrials.gov: NCT03745287",
                        supporting_text="This is a single-arm, open-label, multi-site, single-dose Phase 1/2/3 study.",
                        citation_url=_TRIAL_STUDY_121,
                        limitation="The trial registry record does not resolve all analysis-population and missing-data questions.",
                    ),
                    EvidenceItem(
                        source=EvidenceSource.LITERATURE,
                        maturity=EvidenceMaturity.DIRECT,
                        claim=(
                            "Published assessment notes the absence of randomization, blinding, and a concurrent control."
                        ),
                        source_title="Regulatory Assessment of Casgevy",
                        supporting_text="unable to provide valid probability statements about treatment effects",
                        citation_url=_LITERATURE_ASSESSMENT,
                        limitation="External assessment cannot remove single-arm design bias.",
                    ),
                ],
                known=["The pivotal program was not a conventional randomized controlled trial."],
                unknowns=["The extent to which treatment selection and follow-up maturity affect effect estimates."],
                development_actions=["Predefine analysis populations, handling of intercurrent events, and a comparator strategy."],
            ),
            AxisAssessment(
                axis=EvidenceAxis.RESIDUAL_UNCERTAINTY,
                evidence=[
                    EvidenceItem(
                        source=EvidenceSource.REGULATORY,
                        maturity=EvidenceMaturity.DIRECT,
                        claim=(
                            "The approval basis called for postmarketing studies of off-target editing and "
                            "long-term safety, including malignancy risk."
                        ),
                        source_title="FDA Summary Basis for Regulatory Action: CASGEVY",
                        supporting_text="safety postmarketing requirement studies to assess the off-target editing risks",
                        citation_url=_FDA_LONG_TERM_SAFETY,
                        limitation="Postmarketing requirements identify unresolved questions but do not quantify their probability.",
                    )
                ],
                known=["The approval package explicitly preserved long-term genetic safety uncertainty."],
                unknowns=["Whether registry follow-up will be sufficient to characterize rare adverse outcomes."],
                development_actions=["Translate unresolved risks into candidate-specific assays and follow-up studies."],
            ),
        ],
    )
