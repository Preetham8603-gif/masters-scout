"""Country comparison: weighted scoring over hand-curated factors."""
import pandas as pd
import yaml

from .paths import DATA

FACTORS = {
    "affordability": "Affordability (tuition + living)",
    "post_study_work": "Post-study work visa",
    "ai_jobs": "AI/ML job market",
    "scholarships": "Scholarships for Indians",
    "research_roles": "Paid research roles / funded MS",
    "pr_pathway": "Long-term residence pathway",
    "english": "English-friendly",
}

DEFAULT_WEIGHTS = {
    "affordability": 5,
    "post_study_work": 4,
    "ai_jobs": 4,
    "scholarships": 4,
    "research_roles": 4,
    "pr_pathway": 2,
    "english": 3,
}


def load_countries() -> list[dict]:
    return yaml.safe_load((DATA / "countries.yaml").read_text())["countries"]


def country_names() -> dict[str, str]:
    """ISO code -> country name."""
    return {c["code"]: c["name"] for c in load_countries()}


def score_countries(weights: dict[str, float], countries: list[dict] | None = None) -> pd.DataFrame:
    """Weighted average of 1-5 factor scores, rescaled to 0-100.

    Factors with weight 0 are ignored. Returns rows sorted best first.
    """
    countries = countries if countries is not None else load_countries()
    total_w = sum(w for w in weights.values() if w > 0)
    rows = []
    for c in countries:
        s = c["scores"]
        if total_w == 0:
            score = 0.0
        else:
            avg = sum(s[f] * w for f, w in weights.items() if w > 0) / total_w  # 1..5
            score = (avg - 1) / 4 * 100
        best = sorted(FACTORS, key=lambda f: -s[f] * max(weights.get(f, 0), 0.01))[:2]
        weak = [f for f in FACTORS if s[f] <= 2 and weights.get(f, 0) >= 3]
        rows.append(
            {
                "Country": c["name"],
                "Code": c["code"],
                "Region": c["region"],
                "Score": round(score, 1),
                "Strengths": ", ".join(FACTORS[f] for f in best),
                "Watch out": ", ".join(FACTORS[f] for f in weak) or "-",
                **{FACTORS[f]: s[f] for f in FACTORS},
            }
        )
    return pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)


def load_scholarships() -> pd.DataFrame:
    items = yaml.safe_load((DATA / "scholarships.yaml").read_text())["scholarships"]
    return pd.DataFrame(items)
