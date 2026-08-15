"""Clinical asset derisking for in vivo CRISPR programs.

This is the pre-phase workflow: the input is a clinical asset plus planned trial
design, and the output is a deterministic risk profile that can be rendered,
audited, and iterated with the science team. Scores are intentionally simple at
this stage. They are transparent enough for reviewers to challenge, which is the
point.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from probception.types import Evidence, SourceKind, content_id

ScoreDomain = Literal["cell", "animal", "human"]
ScoreKind = Literal["safety", "efficacy"]


class TrialRecord(BaseModel):
    """Normalized trial facts collected from Paperclip or a fallback seed set."""

    asset: str
    nct_id: str
    name: str
    sponsor: str
    phase: str
    start_date: str
    completion_date: str = ""
    status: str = ""
    enrollment: int | None = None
    cas_system: str = ""
    guide_or_target: str = ""
    delivery: str = ""
    route: str = ""
    notes: list[str] = Field(default_factory=list)
    source: str = "seed"


class DomainScore(BaseModel):
    """One safety or efficacy score on a 0-100 good-is-high scale."""

    kind: ScoreKind
    domain: ScoreDomain
    score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0)
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)


class RiskProfile(BaseModel):
    """The renderable result for a clinical asset."""

    id: str = ""
    asset: str
    planned_trial_design: str
    generated_from: str
    domain_scores: list[DomainScore]
    confidence: float = Field(ge=0.0, le=1.0)
    safety_score: float = Field(ge=0.0, le=100.0)
    efficacy_score: float = Field(ge=0.0, le=100.0)
    risk_score: float = Field(ge=0.0, le=100.0)
    success_score: float = Field(ge=0.0, le=100.0)
    fda_approval_score: float = Field(ge=0.0, le=100.0)
    commercial_success_score: float = Field(ge=0.0, le=100.0)
    status: str
    reasoning: list[str]
    next_data_to_collect: list[str]
    trials: list[TrialRecord]
    evidence: list[Evidence]

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            payload = {
                "asset": self.asset,
                "planned_trial_design": self.planned_trial_design,
                "scores": [(s.kind, s.domain, round(s.score, 3)) for s in self.domain_scores],
            }
            object.__setattr__(self, "id", content_id(payload, "risk"))


_DOMAIN_IMPORTANCE: dict[tuple[ScoreKind, ScoreDomain], float] = {
    ("safety", "cell"): 0.10,
    ("safety", "animal"): 0.20,
    ("safety", "human"): 0.35,
    ("efficacy", "cell"): 0.08,
    ("efficacy", "animal"): 0.12,
    ("efficacy", "human"): 0.15,
}


_SEED_TRIALS: list[TrialRecord] = [
    TrialRecord(
        asset="Casgevy / exa-cel / CTX001",
        nct_id="NCT03745287",
        name="A Safety and Efficacy Study Evaluating CTX001 in Subjects With Severe Sickle Cell Disease",
        sponsor="Vertex Pharmaceuticals Incorporated",
        phase="PHASE2,PHASE3",
        start_date="2018-11-27",
        completion_date="2025-07-07",
        status="COMPLETED",
        enrollment=63,
        cas_system="SpCas9 ex vivo editing of autologous CD34+ HSPCs",
        guide_or_target="BCL11A erythroid enhancer",
        delivery="Electroporation ex vivo; not LNP",
        route="Autologous cell therapy after conditioning",
        notes=[
            "FDA-approved comparator; strong human efficacy but delivery is not in vivo LNP.",
            "Use as regulatory precedent, not as a direct LNP delivery comparator.",
        ],
        source="clinicaltrials.gov",
    ),
    TrialRecord(
        asset="VERVE-101",
        nct_id="NCT05398029",
        name="A Study of VERVE-101 in Patients With Familial Hypercholesterolemia and Cardiovascular Disease",
        sponsor="Verve Therapeutics, Inc.",
        phase="PHASE1",
        start_date="2022-07-05",
        completion_date="2025-02-14",
        status="COMPLETED",
        enrollment=13,
        cas_system="Adenine base editor mRNA",
        guide_or_target="PCSK9",
        delivery="LNP",
        route="Intravenous",
        notes=[
            "Direct in vivo LNP base-editing precedent.",
            "Safety signal history keeps human safety confidence limited.",
        ],
        source="clinicaltrials.gov",
    ),
    TrialRecord(
        asset="VERVE-102",
        nct_id="NCT06164730",
        name="A Study of VERVE-102 in Patients With Familial Hypercholesterolemia or Premature Coronary Artery Disease",
        sponsor="Verve Therapeutics, Inc.",
        phase="PHASE1",
        start_date="2024-04-30",
        completion_date="2027-08",
        status="RECRUITING",
        enrollment=85,
        cas_system="ABE8.8 mRNA",
        guide_or_target="PCSK9",
        delivery="GalNAc-LNP",
        route="Intravenous",
        notes=[
            "Most direct public analogue for planned in vivo LNP PCSK9 editing.",
            "Reported dose-dependent PCSK9 and LDL-C lowering supports efficacy confidence.",
        ],
        source="clinicaltrials.gov",
    ),
    TrialRecord(
        asset="NTLA-2001",
        nct_id="NCT04601051",
        name=(
            "Study to Evaluate Safety, Tolerability, Pharmacokinetics, and "
            "Pharmacodynamics of NTLA-2001 in Patients With ATTR"
        ),
        sponsor="Intellia Therapeutics",
        phase="PHASE1",
        start_date="2020-11-05",
        completion_date="2025-09-12",
        status="COMPLETED",
        enrollment=72,
        cas_system="CRISPR-Cas9 mRNA",
        guide_or_target="TTR",
        delivery="LNP",
        route="Intravenous",
        notes=[
            "Key in vivo CRISPR-Cas9 LNP human precedent.",
            "Trial data include published patient outcome cohorts and redosing signal.",
        ],
        source="clinicaltrials.gov",
    ),
]


_BASELINES: dict[str, dict[str, float]] = {
    "casgevy": {
        "safety_cell": 82,
        "safety_animal": 78,
        "safety_human": 78,
        "efficacy_cell": 92,
        "efficacy_animal": 85,
        "efficacy_human": 95,
        "confidence": 0.88,
        "fda": 100,
        "commercial": 78,
    },
    "verve-101": {
        "safety_cell": 74,
        "safety_animal": 70,
        "safety_human": 48,
        "efficacy_cell": 80,
        "efficacy_animal": 76,
        "efficacy_human": 66,
        "confidence": 0.55,
        "fda": 22,
        "commercial": 48,
    },
    "verve-102": {
        "safety_cell": 78,
        "safety_animal": 76,
        "safety_human": 69,
        "efficacy_cell": 84,
        "efficacy_animal": 80,
        "efficacy_human": 79,
        "confidence": 0.66,
        "fda": 42,
        "commercial": 70,
    },
    "ntla-2001": {
        "safety_cell": 80,
        "safety_animal": 78,
        "safety_human": 73,
        "efficacy_cell": 84,
        "efficacy_animal": 82,
        "efficacy_human": 88,
        "confidence": 0.74,
        "fda": 50,
        "commercial": 68,
    },
}


def seed_trial_records() -> list[TrialRecord]:
    """Return the built-in seed records used when Paperclip is unavailable."""
    return [t.model_copy(deep=True) for t in _SEED_TRIALS]


def score_asset(
    asset: str,
    planned_trial_design: str,
    *,
    trials: list[TrialRecord] | None = None,
    evidence: list[Evidence] | None = None,
) -> RiskProfile:
    """Score a clinical asset deterministically from trial maturity and analogues."""
    matched_trials = _select_trials(asset, trials or seed_trial_records())
    if not matched_trials:
        matched_trials = _select_trials(planned_trial_design, trials or seed_trial_records())
    if not matched_trials:
        matched_trials = seed_trial_records()

    generated_from = _baseline_key(asset, planned_trial_design, matched_trials)
    base = _BASELINES.get(generated_from, _derive_baseline(asset, planned_trial_design, matched_trials))
    ev = evidence or _evidence_from_trials(matched_trials)
    evidence_ids = [e.id for e in ev]

    is_lnp_plan = "lnp" in f"{asset} {planned_trial_design}".lower()
    domain_scores: list[DomainScore] = []
    for kind in ("safety", "efficacy"):
        for domain in ("cell", "animal", "human"):
            key = f"{kind}_{domain}"
            raw_score = base[key]
            score = _adjust_for_fit(raw_score, domain, generated_from, is_lnp_plan)
            confidence = _domain_confidence(base["confidence"], domain, matched_trials)
            weight = _inverse_weight(score, _DOMAIN_IMPORTANCE[(kind, domain)], confidence)
            domain_scores.append(
                DomainScore(
                    kind=kind,  # type: ignore[arg-type]
                    domain=domain,  # type: ignore[arg-type]
                    score=round(score, 1),
                    confidence=round(confidence, 3),
                    weight=round(weight, 4),
                    rationale=_rationale(kind, domain, generated_from, matched_trials, is_lnp_plan),
                    evidence_ids=evidence_ids[:4],
                )
            )

    safety = _weighted_average([s for s in domain_scores if s.kind == "safety"])
    efficacy = _weighted_average([s for s in domain_scores if s.kind == "efficacy"])
    confidence = _overall_confidence(domain_scores)
    fda = _bounded(base["fda"] + _phase_bonus(matched_trials) + (3 if safety >= 70 else -5))
    commercial = _bounded(base["commercial"] + (efficacy - 70) * 0.25 + (confidence - 0.6) * 20)
    success = _bounded(0.32 * safety + 0.34 * efficacy + 0.22 * fda + 0.12 * commercial)
    risk = _bounded(100 - success)

    reasoning = [
        "Human in vivo LNP evidence receives the highest weight; weak scores are upweighted so the risk profile is driven by the bottleneck, not the average.",
        f"Closest public analogue selected: {generated_from}.",
        "Scores are deterministic and can be challenged by replacing seed trial records with Paperclip results.",
    ]
    if is_lnp_plan and generated_from == "casgevy":
        reasoning.append("Casgevy is regulatory proof for CRISPR but not delivery proof for in vivo LNP.")
    if any("safety signal" in " ".join(t.notes).lower() for t in matched_trials):
        reasoning.append("Known safety-signal history pushes human safety and FDA probability down.")

    return RiskProfile(
        asset=asset,
        planned_trial_design=planned_trial_design,
        generated_from=generated_from,
        domain_scores=domain_scores,
        confidence=round(confidence, 3),
        safety_score=round(safety, 1),
        efficacy_score=round(efficacy, 1),
        risk_score=round(risk, 1),
        success_score=round(success, 1),
        fda_approval_score=round(fda, 1),
        commercial_success_score=round(commercial, 1),
        status=_status(success, confidence),
        reasoning=reasoning,
        next_data_to_collect=_next_data_to_collect(domain_scores, matched_trials),
        trials=matched_trials,
        evidence=ev,
    )


def write_risk_report(profile: RiskProfile, root: str | Path = "runs") -> Path:
    """Render a self-contained HTML risk report."""
    out_dir = Path(root) / profile.id
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "risk_profile.json"
    json_path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")

    parts = [
        "<!-- Probception clinical asset risk report -->",
        "<style>",
        "body{margin:0;background:#101214;color:#edf2f7;font:15px/1.55 Arial,sans-serif;padding:28px}",
        ".wrap{max-width:1120px;margin:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}",
        ".kpi,.panel{background:#171b20;border:1px solid #29313a;border-radius:8px;padding:14px}.v{font-size:28px;font-weight:700}",
        ".l{color:#a6b0bb;font-size:12px;text-transform:uppercase}h1{margin:0 0 4px}h2{margin:26px 0 10px;font-size:18px;color:#8bd3ff}",
        "table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #29313a;padding:8px;text-align:left;vertical-align:top}",
        "th{font-size:12px;color:#a6b0bb;text-transform:uppercase}.bar{height:8px;background:#27303a;border-radius:4px;overflow:hidden}.bar i{display:block;height:100%;background:#64d38a}",
        ".mono{font-family:Consolas,monospace;color:#a6b0bb;font-size:12px}.warn{color:#ffd166}.ok{color:#64d38a}.bad{color:#ff7b7b}",
        "</style>",
        "<div class='wrap'>",
        f"<h1>{_esc(profile.asset)}</h1>",
        f"<div class='mono'>{_esc(profile.planned_trial_design)}</div>",
        "<div class='grid' style='margin-top:16px'>",
        _kpi("Success", profile.success_score, profile.status),
        _kpi("Risk", profile.risk_score, "lower is better"),
        _kpi("Safety", profile.safety_score, "0-100"),
        _kpi("Efficacy", profile.efficacy_score, "0-100"),
        _kpi("Confidence", profile.confidence * 100, "evidence maturity"),
        _kpi("FDA approval", profile.fda_approval_score, "probability proxy"),
        _kpi("Commercial", profile.commercial_success_score, "success proxy"),
        "</div>",
        "<h2>Risk Drivers</h2><div class='panel'><table><tr><th>Metric</th><th>Domain</th><th>Score</th><th>Weight</th><th>Why</th></tr>",
    ]
    for s in profile.domain_scores:
        parts.append(
            f"<tr><td>{_esc(s.kind)}</td><td>{_esc(s.domain)}</td><td>{s.score:.1f}{_bar(s.score)}</td>"
            f"<td>{s.weight:.3f}</td><td>{_esc(s.rationale)}</td></tr>"
        )
    parts.extend(["</table></div>", "<h2>Trial Evidence</h2><div class='panel'><table>"])
    parts.append("<tr><th>Name</th><th>Sponsor</th><th>Phase</th><th>Date</th><th>CRISPR + LNP</th></tr>")
    for t in profile.trials:
        parts.append(
            f"<tr><td><b>{_esc(t.asset)}</b><br><span class='mono'>{_esc(t.nct_id)}</span><br>{_esc(t.name)}</td>"
            f"<td>{_esc(t.sponsor)}</td><td>{_esc(t.phase)}</td><td>{_esc(t.start_date)}</td>"
            f"<td>{_esc(t.cas_system)}<br>{_esc(t.guide_or_target)}<br>{_esc(t.delivery)}</td></tr>"
        )
    parts.extend(["</table></div>", "<h2>Agent Reasoning</h2><div class='panel'><ul>"])
    parts.extend(f"<li>{_esc(item)}</li>" for item in profile.reasoning)
    parts.extend(["</ul></div>", "<h2>Next Data To Collect</h2><div class='panel'><ul>"])
    parts.extend(f"<li>{_esc(item)}</li>" for item in profile.next_data_to_collect)
    parts.append("</ul></div></div>")

    out = out_dir / "risk_report.html"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def _select_trials(text: str, trials: list[TrialRecord]) -> list[TrialRecord]:
    hay = text.lower()
    exact = [t for t in trials if t.asset.lower() in hay or t.nct_id.lower() in hay]
    if exact:
        return exact
    hits = [t for t in trials if _trial_matches(hay, t)]
    return hits


def _trial_matches(hay: str, trial: TrialRecord) -> bool:
    aliases = trial.asset.lower().replace("/", " ").split()
    aliases.extend([trial.nct_id.lower(), trial.guide_or_target.lower()])
    if "casgevy" in hay and "casgevy" in trial.asset.lower():
        return True
    return any(a and len(a) > 3 and a in hay for a in aliases)


def _baseline_key(asset: str, design: str, trials: list[TrialRecord]) -> str:
    direct_text = f"{asset} {design}".lower()
    for key in ("casgevy", "verve-101", "verve-102", "ntla-2001"):
        if key in direct_text:
            return key
    text = f"{direct_text} {' '.join(t.asset for t in trials)}".lower()
    for key in _BASELINES:
        if key in text:
            return key
    if "ctx001" in text or "exa-cel" in text:
        return "casgevy"
    if "pcsk9" in text and "lnp" in text:
        return "verve-102"
    if "ttr" in text or "transthyretin" in text:
        return "ntla-2001"
    return "custom"


def _derive_baseline(asset: str, design: str, trials: list[TrialRecord]) -> dict[str, float]:
    text = f"{asset} {design}".lower()
    has_lnp = "lnp" in text
    has_human = any(t.phase for t in trials)
    return {
        "safety_cell": 68,
        "safety_animal": 62 if has_lnp else 58,
        "safety_human": 55 if has_human else 42,
        "efficacy_cell": 66,
        "efficacy_animal": 61,
        "efficacy_human": 52 if has_human else 38,
        "confidence": 0.48 if has_human else 0.35,
        "fda": 18,
        "commercial": 42,
    }


def _evidence_from_trials(trials: list[TrialRecord]) -> list[Evidence]:
    out: list[Evidence] = []
    for trial in trials:
        out.append(
            Evidence(
                kind=SourceKind.CLINICAL_TRIAL,
                source=trial.nct_id,
                claim=(
                    f"{trial.asset}: {trial.phase} {trial.status.lower()} study sponsored by "
                    f"{trial.sponsor}; delivery={trial.delivery}; target={trial.guide_or_target}."
                ),
                strength=_trial_strength(trial),
                meta=trial.model_dump(mode="json"),
            )
        )
    return out


def _trial_strength(trial: TrialRecord) -> float:
    phase = trial.phase.upper()
    if "PHASE3" in phase:
        return 0.9
    if "PHASE2" in phase:
        return 0.75
    if "PHASE1" in phase:
        return 0.62
    return 0.45


def _adjust_for_fit(score: float, domain: ScoreDomain, key: str, is_lnp_plan: bool) -> float:
    if is_lnp_plan and key == "casgevy" and domain in {"animal", "human"}:
        return _bounded(score - 12)
    return _bounded(score)


def _domain_confidence(base: float, domain: ScoreDomain, trials: list[TrialRecord]) -> float:
    bump = {"cell": -0.05, "animal": 0.0, "human": 0.08}[domain]
    if domain == "human" and any("PHASE3" in t.phase.upper() for t in trials):
        bump += 0.08
    return max(0.05, min(0.98, base + bump))


def _inverse_weight(score: float, importance: float, confidence: float) -> float:
    risk = max(0.05, 1.0 - score / 100.0)
    return importance * risk * (0.55 + confidence)


def _weighted_average(scores: list[DomainScore]) -> float:
    denom = sum(s.weight for s in scores) or 1.0
    return sum(s.score * s.weight for s in scores) / denom


def _overall_confidence(scores: list[DomainScore]) -> float:
    denom = sum(s.weight for s in scores) or 1.0
    return sum(s.confidence * s.weight for s in scores) / denom


def _phase_bonus(trials: list[TrialRecord]) -> float:
    phases = " ".join(t.phase.upper() for t in trials)
    if "PHASE3" in phases:
        return 16
    if "PHASE2" in phases:
        return 9
    if "PHASE1" in phases:
        return 3
    return 0


def _rationale(
    kind: str, domain: str, generated_from: str, trials: list[TrialRecord], is_lnp_plan: bool
) -> str:
    trial = trials[0]
    delivery = "direct LNP fit" if "lnp" in trial.delivery.lower() else "not direct LNP delivery"
    fit = f"{generated_from} analogue, {trial.phase}, {delivery}"
    if generated_from == "casgevy" and is_lnp_plan and domain == "human":
        fit += "; penalized for ex vivo delivery mismatch"
    return f"{kind} evidence in {domain}: {fit}."


def _next_data_to_collect(scores: list[DomainScore], trials: list[TrialRecord]) -> list[str]:
    weakest = sorted(scores, key=lambda s: (s.score, -s.weight))[:3]
    items = [
        f"Fill {s.kind}/{s.domain} gap with thresholded evidence before changing the score."
        for s in weakest
    ]
    if not any("lnp" in t.delivery.lower() for t in trials):
        items.append("Add an in vivo LNP comparator; current closest trial is not a delivery match.")
    items.append("Have the science team mark which evidence came from cell, animal, and human data.")
    items.append("Run the same profile through the Claude skill and diff score explanations, not scores.")
    return items


def _status(success: float, confidence: float) -> str:
    if success >= 72 and confidence >= 0.7:
        return "advance"
    if success >= 58:
        return "advance with risk controls"
    if success >= 45:
        return "hold for targeted derisking"
    return "do not advance without new evidence"


def _bounded(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _bar(score: float) -> str:
    return f"<div class='bar'><i style='width:{_bounded(score):.1f}%'></i></div>"


def _kpi(label: str, value: float, sub: str) -> str:
    tone = "ok" if label != "Risk" and value >= 70 else "warn" if value >= 45 else "bad"
    if label == "Risk":
        tone = "ok" if value <= 35 else "warn" if value <= 55 else "bad"
    return (
        f"<div class='kpi'><div class='l'>{_esc(label)}</div>"
        f"<div class='v {tone}'>{value:.1f}</div><div class='mono'>{_esc(sub)}</div></div>"
    )


def _esc(value: object) -> str:
    return html.escape(str(value))


def profile_to_json(profile: RiskProfile) -> str:
    """Pretty JSON for MCP and CLI callers."""
    return json.dumps(profile.model_dump(mode="json"), indent=2)
