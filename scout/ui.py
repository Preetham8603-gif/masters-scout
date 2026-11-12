"""Streamlit helpers shared by all pages."""
import streamlit as st

from . import csrankings, openalex
from .countries import country_names
from .profile import load_profile


def setup(title: str, icon: str = "🎓") -> None:
    st.set_page_config(page_title=f"{title} · Masters Scout", page_icon=icon, layout="wide")
    with st.sidebar:
        u = openalex.usage_today()
        st.caption(f"OpenAlex requests today: **{u['requests']}** (new, not cached)")
        age = csrankings.data_age_days()
        if age is not None:
            st.caption(f"Faculty data: {age:.0f} days old (auto-refreshes monthly)")


def profile():
    if "profile" not in st.session_state:
        st.session_state.profile = load_profile()
    return st.session_state.profile


def country_picker(key: str, label: str = "Countries", default: list[str] | None = None) -> list[str]:
    names = country_names()
    default = [c for c in (default if default is not None else profile().countries) if c in names]
    return st.multiselect(label, options=list(names), default=default, format_func=lambda c: f"{names[c]} ({c})", key=key)


@st.cache_data(show_spinner="Loading faculty data (CSRankings)...", ttl=86400)
def faculty(countries: tuple[str, ...], since_year: int, min_pubs: float):
    return csrankings.load_faculty(list(countries), since_year, min_pubs)


def link(label: str, url) -> str:
    return f"[{label}]({url})" if isinstance(url, str) and url else ""
