"""CSRankings faculty data (https://csrankings.org, data CC BY-NC-ND 4.0, personal use).

Gives us: who is actually faculty, their homepage / Google Scholar / ORCID, and how many
papers they published at top AI venues each year. Downloaded once and refreshed monthly.
"""
import re
import time
import unicodedata

import pandas as pd
import requests

from .paths import CACHE

BASE = "https://raw.githubusercontent.com/emeryberger/CSrankings/gh-pages/"
FILES = {
    "authors.csv": "generated-author-info.csv",
    "institutions.csv": "institutions.csv",
    "csrankings.csv": "csrankings.csv",
}
MAX_AGE_DAYS = 30

# Top venues CSRankings tracks for AI-related areas -> friendly sub-field name
AI_VENUES = {
    "aaai": "AI",
    "ijcai": "AI",
    "icml": "Machine learning",
    "nips": "Machine learning",
    "iclr": "Machine learning",
    "kdd": "Data mining",
    "cvpr": "Computer vision",
    "iccv": "Computer vision",
    "eccv": "Computer vision",
    "acl": "NLP",
    "emnlp": "NLP",
    "naacl": "NLP",
    "sigir": "Information retrieval",
    "www": "Web & IR",
    "icra": "Robotics",
    "iros": "Robotics",
    "rss": "Robotics",
}
SUBFIELDS = sorted(set(AI_VENUES.values()))


def ensure_data(force: bool = False) -> None:
    for local, remote in FILES.items():
        path = CACHE / local
        stale = not path.exists() or (time.time() - path.stat().st_mtime) > MAX_AGE_DAYS * 86400
        if force or stale:
            r = requests.get(BASE + remote, timeout=120)
            r.raise_for_status()
            path.write_bytes(r.content)


def data_age_days() -> float | None:
    p = CACHE / "authors.csv"
    return None if not p.exists() else (time.time() - p.stat().st_mtime) / 86400


def clean_name(name: str) -> str:
    """'A. P. Vinod 0001' -> 'A. P. Vinod' (CSRankings adds DBLP disambiguation numbers)."""
    return re.sub(r"\s+\d{4}$", "", name).strip()


def name_key(name: str) -> str:
    """Normalised 'first last' key for matching names across data sources."""
    name = clean_name(name)
    name = name.replace("ß", "ss")
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[^a-zA-Z\s-]", " ", name).lower().replace("-", " ")
    parts = [p for p in name.split() if len(p) > 1]  # drop initials
    if not parts:
        return ""
    return f"{parts[0]} {parts[-1]}" if len(parts) > 1 else parts[0]


def load_institutions() -> pd.DataFrame:
    ensure_data()
    df = pd.read_csv(CACHE / "institutions.csv")
    df["countryabbrv"] = df["countryabbrv"].str.upper()
    return df


def load_faculty(countries: list[str], since_year: int, min_pubs: float = 1.0) -> pd.DataFrame:
    """Faculty in the given countries with AI-venue papers since `since_year`.

    One row per person with: name, institution, country, AI paper count, sub-field breakdown,
    homepage, scholar, orcid, name_key.
    """
    ensure_data()
    inst = load_institutions()
    inst = inst[inst["countryabbrv"].isin([c.upper() for c in countries])]

    authors = pd.read_csv(CACHE / "authors.csv")
    authors = authors[authors["area"].isin(AI_VENUES) & (authors["year"] >= since_year)]
    authors = authors.merge(inst[["institution", "countryabbrv"]], left_on="dept", right_on="institution")
    if authors.empty:
        return pd.DataFrame()
    authors["subfield"] = authors["area"].map(AI_VENUES)

    totals = authors.groupby(["name", "dept", "countryabbrv"], as_index=False).agg(
        ai_papers=("count", "sum"), adjusted=("adjustedcount", "sum"), last_year=("year", "max")
    )
    by_sub = authors.pivot_table(index=["name", "dept"], columns="subfield", values="count", aggfunc="sum", fill_value=0)

    def top_subfields(row) -> str:
        nz = row[row > 0].sort_values(ascending=False)
        return ", ".join(f"{k} ({int(v)})" for k, v in nz.head(3).items())

    subs = by_sub.apply(top_subfields, axis=1).rename("subfields").reset_index()
    fac = totals.merge(subs, on=["name", "dept"])
    fac = fac.merge(by_sub.reset_index(), on=["name", "dept"])

    info = pd.read_csv(CACHE / "csrankings.csv")
    info = info.drop_duplicates(subset=["name", "affiliation"])
    fac = fac.merge(info, left_on=["name", "dept"], right_on=["name", "affiliation"], how="left")

    fac = fac[fac["ai_papers"] >= min_pubs].copy()
    fac["display_name"] = fac["name"].map(clean_name)
    fac["name_key"] = fac["name"].map(name_key)
    fac["orcid"] = fac["orcid"].where(~fac["orcid"].fillna("").str.startswith("0000-0000-0000"), None)
    fac["scholar_url"] = fac["scholarid"].map(
        lambda s: f"https://scholar.google.com/citations?user={s}" if isinstance(s, str) and s != "NOSCHOLARPAGE" else None
    )
    fac = fac.rename(columns={"dept": "institution", "countryabbrv": "country"})
    keep = ["display_name", "name", "institution", "country", "ai_papers", "adjusted", "last_year",
            "subfields", "homepage", "scholar_url", "orcid", "name_key"] + [s for s in SUBFIELDS if s in fac.columns]
    return fac[keep].sort_values("adjusted", ascending=False).reset_index(drop=True)


def institution_strength(faculty: pd.DataFrame) -> pd.DataFrame:
    """Aggregate faculty table to one row per institution."""
    if faculty.empty:
        return pd.DataFrame()
    g = faculty.groupby(["institution", "country"])
    out = g.agg(ai_faculty=("name", "count"), ai_papers=("ai_papers", "sum"), adjusted=("adjusted", "sum")).reset_index()
    subs = [s for s in SUBFIELDS if s in faculty.columns]
    sub_tot = g[subs].sum()
    out["top_areas"] = [
        ", ".join(sub_tot.loc[(r.institution, r.country)].sort_values(ascending=False).head(3).index)
        for r in out.itertuples()
    ]
    out = out.sort_values("adjusted", ascending=False).reset_index(drop=True)
    out.insert(0, "ai_research_rank", range(1, len(out) + 1))
    return out
