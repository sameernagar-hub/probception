"""The regulatory evidence-map smoke fixture stays complete and auditable."""

from __future__ import annotations

import json

from probception.evidence_map import (
    EvidenceAxis,
    EvidenceSource,
    SourceAvailability,
    casgevy_smoke_map,
    render_evidence_map,
    write_evidence_map,
)


def test_casgevy_smoke_map_covers_every_axis_and_source_bucket():
    evidence_map = casgevy_smoke_map()

    assert evidence_map.product == "CASGEVY (exagamglogene autotemcel)"
    assert {assessment.axis for assessment in evidence_map.axes} == set(EvidenceAxis)
    assert len(evidence_map.axes) == len(EvidenceAxis)
    assert all(assessment.evidence for assessment in evidence_map.axes)
    assert all(
        item.citation_url.startswith("https://paperclip.gxl.ai/citations/")
        for assessment in evidence_map.axes
        for item in assessment.evidence
    )
    assert all(
        item.source_title and item.supporting_text
        for assessment in evidence_map.axes
        for item in assessment.evidence
    )

    sources = {search.source: search for search in evidence_map.source_searches}
    assert set(sources) == set(EvidenceSource)
    assert sources[EvidenceSource.CLIPBOARD].availability is SourceAvailability.NOT_PROVIDED
    assert sources[EvidenceSource.LITERATURE].documents_found > 0
    assert sources[EvidenceSource.TRIALS].documents_found > 0
    assert sources[EvidenceSource.REGULATORY].documents_found > 0


def test_casgevy_smoke_map_keeps_direct_evidence_separate_from_analogy():
    evidence_map = casgevy_smoke_map()

    for assessment in evidence_map.axes:
        assert assessment.known
        assert assessment.unknowns
        assert assessment.development_actions
        assert all(item.maturity.value in {"direct", "analog", "inferred"} for item in assessment.evidence)


def test_rendered_map_includes_specific_source_text_for_every_citation():
    evidence_map = casgevy_smoke_map()
    report = render_evidence_map(evidence_map)

    assert "## Source search coverage" in report
    for assessment in evidence_map.axes:
        assert f"## {assessment.axis.value.replace('_', ' ').title()}" in report
        for item in assessment.evidence:
            assert item.source_title in report
            assert item.supporting_text in report
            assert item.citation_url in report


def test_writer_persists_markdown_and_json_artifacts(tmp_path):
    evidence_map = casgevy_smoke_map()
    markdown_path, json_path = write_evidence_map(evidence_map, tmp_path)

    assert markdown_path.name == "casgevy-evidence-map.md"
    assert json_path.name == "casgevy-evidence-map.json"
    assert markdown_path.read_text(encoding="utf-8") == render_evidence_map(evidence_map)
    assert json.loads(json_path.read_text(encoding="utf-8"))["product"] == evidence_map.product
