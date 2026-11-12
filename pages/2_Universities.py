import streamlit as st

from scout import universities as U
from scout.countries import country_names
from scout.csrankings import institution_strength, load_institutions
from scout.ui import country_picker, faculty, setup

setup("Universities", "🏛️")
names = country_names()
st.title("🏛️ Universities")
st.caption(
    "**AI research rank** is based on CSRankings: papers at top AI, ML, vision, NLP and robotics conferences, "
    "weighted by number of co-authors, within the countries you selected. QS / THE / ARWU ranks come from you, in the table at the bottom."
)

c1, c2, c3 = st.columns([3, 1, 1])
with c1:
    countries = country_picker("uni_countries")
since = c2.selectbox("Research since", [2019, 2020, 2021, 2022, 2023], index=2)
min_fac = c3.number_input("Min. AI faculty", 1, 50, 2)
if not countries:
    st.info("Pick at least one country.")
    st.stop()

fac = faculty(tuple(sorted(countries)), since, 1.0)
strength = institution_strength(fac)
if strength.empty:
    st.warning("No universities found.")
    st.stop()
strength = strength[strength["ai_faculty"] >= min_fac]
homepages = load_institutions().set_index("institution")["homepage"]
df = U.merge(strength)
df["dept_page"] = df["institution"].map(homepages)
df["country"] = df["country"].map(lambda c: names.get(c, c))

f1, f2 = st.columns(2)
use_rank = f1.toggle("Only top-ranked overall (needs your QS/THE ranks)", value=False)
max_rank = f2.number_input("Max overall rank", 50, 1000, 500, step=50, disabled=not use_rank)
if use_rank:
    keep_unranked = st.checkbox("Also keep universities I haven't ranked yet", value=True)
    df = U.filter_top(df, max_rank, keep_unranked)

st.write(f"**{len(df)} universities**")
st.dataframe(
    df[["ai_research_rank", "institution", "country", "ai_faculty", "ai_papers", "top_areas",
        "best_overall_rank", "qs_rank", "the_rank", "arwu_rank", "dept_page"]],
    hide_index=True,
    use_container_width=True,
    column_config={
        "ai_research_rank": "AI rank",
        "ai_faculty": "AI faculty",
        "ai_papers": "Top-AI papers",
        "best_overall_rank": "Best overall rank",
        "dept_page": st.column_config.LinkColumn("CS dept", display_text="open"),
    },
)

st.subheader("Shortlist")
current = [u for u in st.session_state.get("shortlist_unis", []) if u in set(df["institution"])]
sl = st.multiselect("Universities to focus on (the Professors page can filter to these)", df["institution"].tolist(), current)
st.session_state.shortlist_unis = sl

st.subheader("Add overall ranks (QS / THE / ARWU)")
st.caption(
    "These ranking lists aren't free to download automatically, so type the ranks in from "
    "[QS](https://www.topuniversities.com/world-university-rankings), "
    "[THE](https://www.timeshighereducation.com/world-university-rankings) or [ARWU](https://www.shanghairanking.com/rankings/arwu/2025). "
    "Ranked bands like 401-410 → use the first number. Saved to data/rankings.csv."
)
existing = U.load_rankings()
editor_df = df[["institution"]].merge(existing, on="institution", how="left")
for c in U.RANK_COLS:
    editor_df[c] = editor_df[c].astype("Int64")
editor_df["notes"] = editor_df["notes"].fillna("")
edited = st.data_editor(editor_df, hide_index=True, use_container_width=True, disabled=["institution"], key="rank_editor")
if st.button("Save ranks", type="primary"):
    others = existing[~existing["institution"].isin(edited["institution"])]
    import pandas as pd

    U.save_rankings(pd.concat([others, edited], ignore_index=True))
    st.success("Saved.")
    st.rerun()
