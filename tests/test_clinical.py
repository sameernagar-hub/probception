"""Clinical derisking stays deterministic and renderable."""

from __future__ import annotations

import json
import subprocess
import sys

from probception.adapters.base import ExperimentAdapter, SearchAdapter
from probception.adapters.fallback import ResilientExperimentAdapter, ResilientSearchAdapter
from probception.clinical import score_asset, seed_trial_records, write_risk_report
from probception.types import Experiment, Observation, Outcome


def test_risk_profile_scores_known_lnp_asset():
    profile = score_asset(
        "VERVE-102 PCSK9 GalNAc-LNP",
        "Phase 1b/2 single ascending dose in HeFH; safety, PCSK9, and LDL-C endpoints.",
    )
    assert profile.generated_from == "verve-102"
    assert profile.safety_score > 0
    assert profile.efficacy_score > 0
    assert 0 <= profile.risk_score <= 100
    assert {score.domain for score in profile.domain_scores} == {"cell", "animal", "human"}
    assert {score.kind for score in profile.domain_scores} == {"safety", "efficacy"}


def test_casgevy_is_penalized_as_lnp_delivery_comparator():
    profile = score_asset(
        "Casgevy LNP bridge comparator",
        "Use as precedent for an in vivo LNP trial design.",
    )
    human_safety = [
        score for score in profile.domain_scores if score.kind == "safety" and score.domain == "human"
    ][0]
    assert profile.generated_from == "casgevy"
    assert human_safety.score < 78
    assert "delivery mismatch" in " ".join(profile.reasoning + [human_safety.rationale])


def test_risk_report_is_self_contained(tmp_path):
    profile = score_asset("NTLA-2001", "Phase 1 in vivo LNP CRISPR-Cas9 ATTR trial.")
    report = write_risk_report(profile, tmp_path)
    html = report.read_text(encoding="utf-8")
    assert report.exists()
    assert "http://" not in html and "https://" not in html
    assert (report.parent / "risk_profile.json").exists()


def test_paperclip_mcp_lists_tools():
    message = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    result = subprocess.run(
        [sys.executable, "scripts/paperclip_mcp.py"],
        input=json.dumps(message) + "\n",
        capture_output=True,
        text=True,
        check=True,
    )
    body = json.loads(result.stdout)
    names = {tool["name"] for tool in body["result"]["tools"]}
    assert {"paperclip_search", "gather_crispr_trial_data", "score_clinical_asset"} <= names


def test_seed_trials_include_requested_assets():
    assets = {trial.asset for trial in seed_trial_records()}
    assert any("Casgevy" in asset for asset in assets)
    assert "VERVE-101" in assets
    assert "VERVE-102" in assets
    assert "NTLA-2001" in assets


def test_search_fallback_preserves_failure_reason():
    class BrokenSearch(SearchAdapter):
        name = "broken-search"

        def search(self, query: str, limit: int = 10):
            raise RuntimeError("network down")

    evidence = ResilientSearchAdapter(BrokenSearch()).search("CRISPR LNP", limit=2)
    assert evidence
    assert evidence[0].meta["fallback_from"] == "broken-search"
    assert "network down" in evidence[0].meta["fallback_reason"]


def test_experiment_fallback_preserves_valid_outcome():
    class BrokenLab(ExperimentAdapter):
        name = "broken-lab"

        def run(self, experiment: Experiment) -> Observation:
            raise RuntimeError("job failed")

    experiment = Experiment(
        title="assay",
        protocol="run it",
        outcomes=[Outcome(label="positive"), Outcome(label="negative")],
        likelihoods={"h": {"positive": 0.5, "negative": 0.5}},
    )
    observation = ResilientExperimentAdapter(BrokenLab()).run(experiment)
    assert observation.outcome_label in {"positive", "negative"}
    assert observation.raw["fallback_from"] == "broken-lab"
    assert "job failed" in observation.raw["fallback_reason"]


def test_experiment_fallback_rejects_undeclared_live_outcome():
    class InvalidLab(ExperimentAdapter):
        name = "invalid-lab"

        def run(self, experiment: Experiment) -> Observation:
            return Observation(experiment_id=experiment.id, outcome_label="maybe")

    experiment = Experiment(
        title="assay",
        protocol="run it",
        outcomes=[Outcome(label="positive"), Outcome(label="negative")],
        likelihoods={"h": {"positive": 0.5, "negative": 0.5}},
    )
    observation = ResilientExperimentAdapter(InvalidLab()).run(experiment)
    assert observation.outcome_label in {"positive", "negative"}
    assert "undeclared outcome" in observation.raw["fallback_reason"]
