from datetime import date

import pandas as pd
import streamlit as st

from scout import openalex
from scout.profile import save_profile
from scout.ui import country_picker, profile, setup

setup("Explore interests", "🧭")
p = profile()
st.title("🧭 Explore research interests")
st.write(
    "Not sure what to specialise in yet? That's normal. This page lists AI research topics with how much they are growing. "
    "Open a few, skim the top papers, and **add the ones you like to your interests**. The Professors page will then match on them."
)

year = date.today().year
try:
    with st.spinner("Loading topic statistics (cached after the first time)..."):
        recent = openalex.topic_counts(f"{year - 2}-01-01")
        older = openalex.topic_counts(f"{year - 5}-01-01", f"{year - 4}-12-31")
        topics = {t["id"].rsplit("/", 1)[-1]: t for t in openalex.ai_topics()}
except openalex.BudgetError as e:
    st.error(str(e))
    st.stop()

rows = []
for tid, r in recent.items():
    t = topics.get(tid, {})
    old = older.get(tid, {}).get("count", 0)
    rows.append(
        {
            "id": tid,
            "Topic": r["name"],
            f"Papers {year - 2}-{year}": r["count"],
            "Growth vs 3 yrs earlier": (r["count"] / old) if old else None,
            "Keywords": ", ".join(k["display_name"] for k in t.get("keywords", [])[:6]),
            "description": t.get("description", ""),
        }
    )
df = pd.DataFrame(rows)

a, b = st.columns(2)
sort = a.radio("Sort by", ["Fastest growing", "Most papers"], horizontal=True)
min_papers = b.select_slider("Hide small / side topics (min. recent papers)", [0, 1000, 5000, 10000, 20000], 10000)
df = df[df[f"Papers {year - 2}-{year}"] >= min_papers]
df = df.sort_values("Growth vs 3 yrs earlier" if sort == "Fastest growing" else f"Papers {year - 2}-{year}", ascending=False)
search = st.text_input("Filter topics", placeholder="e.g. language, robot, medical, graph")
if search:
    m = df["Topic"].str.contains(search, case=False) | df["Keywords"].str.contains(search, case=False)
    df = df[m]

st.dataframe(
    df.drop(columns=["id", "description"]),
    hide_index=True,
    use_container_width=True,
    column_config={"Growth vs 3 yrs earlier": st.column_config.NumberColumn(format="%.1fx")},
)

st.subheader("Look closer")
choice = st.selectbox("Topic", df["Topic"].tolist())
if choice:
    row = df[df["Topic"] == choice].iloc[0]
    st.write(row["description"])
    st.caption("Keywords: " + row["Keywords"])
    countries = country_picker("explore_countries", "Show top papers from these countries")
    if st.button("Show most-cited recent papers"):
        try:
            ws = openalex.topic_top_works(row["id"], countries, year - 2)
            for w in ws:
                insts = sorted({i["display_name"] for a in w["authorships"] for i in a.get("institutions", [])
                                if not countries or i.get("country_code") in countries})[:3]
                st.markdown(f"- [{w['title']}]({openalex.work_url(w)}) ({w['publication_year']}, {w['cited_by_count']} citations) · {', '.join(insts)}")
        except openalex.BudgetError as e:
            st.error(str(e))
    if st.button(f"➕ Add '{choice}' to my interests", type="primary"):
        if choice not in p.interests:
            p.interests.append(choice)
            save_profile(p)
        st.success(f"Your interests: {', '.join(p.interests)}")

if p.interests:
    st.info("Current interests: " + ", ".join(p.interests) + ". Edit them on the Home page.")
