import pandas as pd
import streamlit as st

from scout import openalex
from scout.countries import country_names
from scout.csrankings import SUBFIELDS
from scout.matcher import encoder_name, find_professors
from scout.outreach import add_contact, connect
from scout.ui import country_picker, faculty, link, profile, setup

setup("Professors", "🧑‍🏫")
p = profile()
names = country_names()

st.title("🧑‍🏫 Find professors")
st.caption(
    "Faculty come from **CSRankings** (people who publish at top AI conferences). Papers come from **OpenAlex**. "
    "Read at least one paper before you email anyone."
)

c1, c2, c3 = st.columns([3, 1, 1])
with c1:
    countries = country_picker("prof_countries")
since = c2.selectbox("Papers since", [2020, 2021, 2022, 2023, 2024], index=3)
min_pubs = c3.number_input("Min. top-AI papers", 1, 50, 3, help="Filters out people with very few top-venue papers in this period")

if not countries:
    st.info("Pick at least one country.")
    st.stop()

fac = faculty(tuple(sorted(countries)), since, float(min_pubs))
if fac.empty:
    st.warning("No faculty found for these filters.")
    st.stop()

uni_filter = st.session_state.get("shortlist_unis", [])
if uni_filter:
    only = st.toggle(f"Only my shortlisted universities ({len(uni_filter)})", value=True)
    if only:
        fac = fac[fac["institution"].isin(uni_filter)]

tab_match, tab_browse = st.tabs(["🎯 Match my interests", "📚 Browse by area"])

con = connect()


def add_button(prof: dict, key: str):
    if st.button("➕ Add to outreach", key=key):
        added = add_contact(con, prof)
        st.toast(f"Added {prof['name']}" if added else f"{prof['name']} is already in your tracker")


with tab_match:
    default_q = p.query_text()
    q = st.text_area(
        "What would you like to work on?",
        default_q,
        placeholder="e.g. reasoning in large language models, efficient inference, retrieval-augmented generation",
        help="Write naturally. A sentence or two works better than a single word.",
    )
    a, b = st.columns([1, 3])
    depth = a.selectbox("Search depth", [1, 2, 3], index=1, help="Pages of 200 papers to scan. Each page is 1 OpenAlex request.")
    b.caption(f"Matching engine: {encoder_name()}. Today's OpenAlex requests: {openalex.usage_today()['requests']}")

    if st.button("Find professors", type="primary", disabled=not q.strip()):
        try:
            with st.spinner("Searching recent papers and matching faculty..."):
                st.session_state.prof_results = find_professors(q, fac, countries, since, pages=depth)
                st.session_state.prof_query = q
        except openalex.BudgetError as e:
            st.error(str(e))

    res: pd.DataFrame = st.session_state.get("prof_results", pd.DataFrame())
    if not res.empty:
        res = res[res["country"].isin(countries)]
        f1, f2 = st.columns(2)
        unis = f1.multiselect("Filter by university", sorted(res["institution"].unique()))
        n_show = f2.slider("Show top", 5, min(100, max(5, len(res))), min(20, len(res)))
        if unis:
            res = res[res["institution"].isin(unis)]
        st.write(f"**{len(res)} professors** matched *{st.session_state.get('prof_query', '')[:80]}*")
        for i, r in res.head(n_show).iterrows():
            with st.container(border=True):
                h1, h2 = st.columns([5, 1])
                h1.markdown(
                    f"### {r['name']}  \n**{r['institution']}**, {names.get(r['country'], r['country'])} · "
                    + " · ".join(x for x in [link("Homepage", r["homepage"]), link("Google Scholar", r["scholar_url"]),
                                             link("OpenAlex", r["openalex_id"])] if x)
                )
                h2.metric("Match", f"{r['match']}%")
                st.caption(
                    f"Areas: {r['subfields']} · {r['ai_papers_total']} top-AI papers since {since} · "
                    f"{r['matching_papers']} papers related to your query · **Overlap:** {r['why']}"
                )
                for paper in r["papers"][:5]:
                    st.markdown(f"- [{paper['title']}]({paper['url']}) ({paper['year']}, {paper['cited_by']} citations)")
                add_button(r.to_dict(), key=f"add_{i}_{r['name']}")
        st.caption("Not verified: a professor may have moved universities or stopped taking students. Check their homepage.")

with tab_browse:
    st.write("Browse active AI faculty by area. No OpenAlex requests needed, so this is good for exploring.")
    area = st.selectbox("Area", SUBFIELDS, index=SUBFIELDS.index("Machine learning"))
    sub = fac[fac.get(area, 0) > 0].sort_values(area, ascending=False) if area in fac.columns else fac.iloc[0:0]
    st.write(f"{len(sub)} faculty with {area} papers since {since}")
    show = sub.head(200)[["display_name", "institution", "country", area, "ai_papers", "subfields", "homepage", "scholar_url"]]
    st.dataframe(
        show.rename(columns={"display_name": "Name", area: f"{area} papers", "ai_papers": "All AI papers"}),
        hide_index=True,
        use_container_width=True,
        column_config={
            "homepage": st.column_config.LinkColumn("Homepage", display_text="open"),
            "scholar_url": st.column_config.LinkColumn("Scholar", display_text="open"),
        },
    )
    pick = st.selectbox("Add someone to outreach", [""] + [f"{r.display_name} | {r.institution}" for r in sub.head(200).itertuples()])
    if pick:
        nm, inst = pick.split(" | ", 1)
        row = sub[(sub["display_name"] == nm) & (sub["institution"] == inst)].iloc[0]
        add_button(
            {"name": nm, "institution": inst, "country": row["country"], "homepage": row["homepage"] if isinstance(row["homepage"], str) else None,
             "scholar_url": row["scholar_url"], "papers": []},
            key=f"browse_add_{pick}",
        )
