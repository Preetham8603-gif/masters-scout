"""University table: CSRankings AI strength + optional overall ranks typed in by the user."""
import pandas as pd

from .paths import RANKINGS_FILE

RANK_COLS = ["qs_rank", "the_rank", "arwu_rank"]


def load_rankings() -> pd.DataFrame:
    if RANKINGS_FILE.exists():
        df = pd.read_csv(RANKINGS_FILE)
    else:
        df = pd.DataFrame(columns=["institution"] + RANK_COLS + ["notes"])
    for c in RANK_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    df["notes"] = df["notes"].fillna("").astype(str)
    return df


def save_rankings(df: pd.DataFrame) -> None:
    df = df[["institution"] + RANK_COLS + ["notes"]].copy()
    has_data = df[RANK_COLS].notna().any(axis=1) | (df["notes"].fillna("").str.strip() != "")
    df[has_data].to_csv(RANKINGS_FILE, index=False)


def merge(strength: pd.DataFrame) -> pd.DataFrame:
    """Add the user's QS / THE / ARWU ranks and a 'best overall rank' column."""
    ranks = load_rankings()
    out = strength.merge(ranks, on="institution", how="left")
    for c in RANK_COLS:
        out[c] = out[c].astype("Int64")
    out["notes"] = out["notes"].fillna("")
    out["best_overall_rank"] = out[RANK_COLS].min(axis=1).astype("Int64")
    return out


def filter_top(df: pd.DataFrame, max_rank: int, include_unranked: bool) -> pd.DataFrame:
    has = df["best_overall_rank"].notna()
    keep = has & (df["best_overall_rank"].fillna(10**6) <= max_rank)
    if include_unranked:
        keep |= ~has
    return df[keep]
