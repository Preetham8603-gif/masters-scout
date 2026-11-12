"""Match the student's interests to faculty, using OpenAlex papers + CSRankings faculty list.

Steps:
1. OpenAlex relevance search for the interest text (recent papers, selected countries).
2. Every author on those papers who is in the CSRankings faculty table (matched by ORCID,
   else by name + institution) becomes a candidate; their matching papers are collected.
3. Rank candidates by semantic similarity of their matching paper titles to the interests
   (local sentence-transformers model, TF-IDF fallback), how many matching papers they have,
   and their overall AI publication record.
"""
import math
import re
from collections import defaultdict
from functools import lru_cache

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

from . import openalex
from .csrankings import name_key

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

STOPWORDS = set(
    """a an and are as at be by for from in into is it of on or that the to with using via based towards toward
    we our their its this these those learning model models deep neural network networks approach method methods
    data new study analysis paper i am want work interested interest""".split()
)


@lru_cache(maxsize=1)
def _encoder():
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(MODEL_NAME)
    except Exception:  # offline first run / install problem -> TF-IDF fallback
        return None


def encoder_name() -> str:
    return "MiniLM sentence embeddings (local)" if _encoder() is not None else "TF-IDF keywords (fallback)"


def similarities(query: str, texts: list[str]) -> np.ndarray:
    """Cosine similarity of `query` to each text, in [0, 1]-ish."""
    if not texts:
        return np.array([])
    enc = _encoder()
    if enc is not None:
        vecs = enc.encode([query] + texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
        return vecs[1:] @ vecs[0]
    from sklearn.feature_extraction.text import TfidfVectorizer

    m = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform([query] + texts)
    return (m[1:] @ m[0].T).toarray().ravel()


def keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9\-]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def _orcid(s) -> str | None:
    if not isinstance(s, str) or not s:
        return None
    return s.rsplit("/", 1)[-1]


def build_faculty_index(faculty: pd.DataFrame):
    by_orcid = {}
    by_name = defaultdict(list)
    for i, row in faculty.iterrows():
        o = _orcid(row.get("orcid"))
        if o:
            by_orcid[o] = i
        if row["name_key"]:
            by_name[row["name_key"]].append(i)
    return by_orcid, by_name


def match_author(authorship: dict, faculty: pd.DataFrame, by_orcid: dict, by_name: dict) -> int | None:
    """Return the faculty row index for an OpenAlex authorship, or None."""
    o = _orcid(authorship.get("author", {}).get("orcid"))
    if o and o in by_orcid:
        return by_orcid[o]
    key = name_key(authorship.get("author", {}).get("display_name", ""))
    cands = by_name.get(key, [])
    if not cands:
        return None
    insts = [i.get("display_name", "") for i in authorship.get("institutions", [])]
    insts += authorship.get("raw_affiliation_strings", []) or []
    best, best_score = None, 0
    for idx in cands:
        fi = faculty.at[idx, "institution"]
        s = max((fuzz.token_set_ratio(fi, x) for x in insts), default=0)
        if s > best_score:
            best, best_score = idx, s
    # Same normalised name AND a similar institution string
    return best if best_score >= 70 else None


def find_professors(query: str, faculty: pd.DataFrame, countries: list[str], since_year: int, pages: int = 2) -> pd.DataFrame:
    """Rank faculty for the interest `query`. Returns one row per professor, best first."""
    works = openalex.search_works(query, countries, since_year, pages=pages)
    if faculty.empty or not works:
        return pd.DataFrame()
    by_orcid, by_name = build_faculty_index(faculty)
    wanted = {c.upper() for c in countries}

    hits = defaultdict(lambda: {"works": {}, "openalex_ids": set(), "last_author": 0})
    for w in works:
        n_auth = len(w.get("authorships", []))
        for pos, a in enumerate(w.get("authorships", [])):
            if not ({i.get("country_code") for i in a.get("institutions", [])} & wanted):
                continue
            idx = match_author(a, faculty, by_orcid, by_name)
            if idx is None:
                continue
            h = hits[idx]
            h["works"][w["id"]] = w
            h["openalex_ids"].add(a["author"]["id"])
            if pos == n_auth - 1 and n_auth > 1:
                h["last_author"] += 1  # senior author position, typical for professors

    if not hits:
        return pd.DataFrame()

    all_titles = sorted({w["id"]: w.get("title") or "" for h in hits.values() for w in h["works"].values()}.items())
    sims = dict(zip([k for k, _ in all_titles], similarities(query, [t for _, t in all_titles])))
    qwords = keywords(query)

    rows = []
    for idx, h in hits.items():
        f = faculty.loc[idx]
        ws = sorted(h["works"].values(), key=lambda w: -sims.get(w["id"], 0))
        top = [sims.get(w["id"], 0) for w in ws[:3]]
        relevance = float(np.mean(top))
        overlap = set()
        for w in ws[:5]:
            overlap |= keywords(w.get("title") or "") & qwords
        topics = [w["primary_topic"]["display_name"] for w in ws if w.get("primary_topic")]
        score = (
            0.65 * relevance
            + 0.20 * min(math.log1p(len(ws)) / math.log1p(8), 1)
            + 0.10 * min(math.log1p(f["adjusted"]) / math.log1p(30), 1)
            + 0.05 * min(h["last_author"] / 2, 1)
        )
        rows.append(
            {
                "match": round(100 * score),
                "name": f["display_name"],
                "institution": f["institution"],
                "country": f["country"],
                "matching_papers": len(ws),
                "ai_papers_total": int(f["ai_papers"]),
                "last_active": int(f["last_year"]),
                "subfields": f["subfields"],
                "homepage": f["homepage"] if isinstance(f["homepage"], str) else None,
                "scholar_url": f["scholar_url"],
                "openalex_id": sorted(h["openalex_ids"])[0],
                "why": ", ".join(sorted(overlap)) or "related topics",
                "topics": ", ".join(dict.fromkeys(topics).keys()) if topics else "",
                "papers": [
                    {
                        "title": w.get("title"),
                        "year": w.get("publication_year"),
                        "url": openalex.work_url(w),
                        "similarity": round(float(sims.get(w["id"], 0)), 2),
                        "cited_by": w.get("cited_by_count", 0),
                    }
                    for w in ws[:6]
                ],
            }
        )
    return pd.DataFrame(rows).sort_values("match", ascending=False).reset_index(drop=True)
