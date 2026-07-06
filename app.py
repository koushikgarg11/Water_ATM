import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------- CONFIG ---
st.set_page_config(
    page_title="Water ATM Downtime Atlas — India",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

INK = "#0C2124"
TEAL = "#155E5A"
TEAL_BRIGHT = "#2F9C8F"
AMBER = "#C9772E"
AMBER_BRIGHT = "#E08F3C"
SLATE = "#4B5A5A"
PAPER = "#ECEAE0"
PAPER2 = "#F5F4EC"
LINE = "#C9C6B6"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background-color: {PAPER}; }}
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

/* --- Streamlit's own fixed header sits ON TOP of the page content with a
   transparent background. The default block-container padding-top exists
   specifically to clear it. Give it a solid matching background AND keep
   enough top padding on our content, or custom headers get clipped/hidden
   underneath the platform's Share/star/GitHub toolbar. --- */
[data-testid="stHeader"] {{
    background-color: {PAPER};
    height: 3.4rem;
}}
.block-container {{
    padding-top: 4.4rem;   /* clears the fixed header, was previously too small */
    max-width: 1400px;
}}

[data-testid="stSidebar"] {{ background-color: {INK}; }}
[data-testid="stSidebar"] * {{ color: #EAF3F1 !important; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(234,243,241,0.15); }}

/* ---- top masthead ---- */
.masthead {{
    background: {INK}; color: #EAF3F1; padding: 30px 38px 0; border-radius: 8px 8px 0 0;
    margin-bottom: 0;
}}
.masthead__row {{ display:flex; justify-content:space-between; align-items:flex-start; gap: 24px; flex-wrap:wrap; }}
.masthead .eyebrow {{
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: .12em;
    color: {TEAL_BRIGHT}; text-transform: uppercase; margin-bottom: 8px;
}}
.masthead h1 {{
    font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 38px;
    margin: 0 0 8px; line-height: 1.15; color: #fff;
}}
.masthead p {{ color: #C3D6D2; max-width: 620px; font-size: 14px; margin:0 0 22px; }}
.masthead__badge {{
    font-family: 'IBM Plex Mono', monospace; font-size: 10.5px; color: #9FB6B2;
    border: 1px solid rgba(234,243,241,0.25); border-radius: 20px; padding: 6px 14px;
    white-space: nowrap; text-align:center;
}}
.masthead__badge b {{ color: {TEAL_BRIGHT}; display:block; font-size:15px; font-family:'Space Grotesk',sans-serif; }}

/* ---- tab bar styled as a real site nav ---- */
.stTabs [data-baseweb="tab-list"] {{
    background: {INK}; gap: 2px; padding: 0 38px; border-radius: 0 0 8px 8px;
    border-bottom: 3px solid {TEAL}; margin-bottom: 22px;
}}
.stTabs [data-baseweb="tab"] {{
    height: 46px; color: #9FB6B2 !important; font-family: 'IBM Plex Mono', monospace;
    font-size: 12.5px; text-transform: uppercase; letter-spacing: .04em;
    background: transparent; border: none;
}}
.stTabs [aria-selected="true"] {{
    color: #fff !important; border-bottom: 3px solid {TEAL_BRIGHT} !important;
    background: rgba(234,243,241,0.06);
}}

/* ---- KPI cards ---- */
.kpi-card {{
    background: {PAPER2}; border: 1px solid {LINE}; border-radius: 6px;
    padding: 16px 18px; text-align:left; height:100%;
}}
.kpi-value {{ font-family: 'Space Grotesk', sans-serif; font-weight:700; font-size: 30px; color: {INK}; }}
.kpi-value--flag {{ color: {AMBER}; }}
.kpi-label {{ font-family: 'IBM Plex Mono', monospace; font-size: 10.5px; text-transform: uppercase;
    letter-spacing: .05em; color: {SLATE}; margin-top:2px; }}

.section-title {{ font-family: 'Space Grotesk', sans-serif; font-weight:700; font-size:20px; color:{INK}; margin: 4px 0 2px;}}
.section-hint {{ font-size: 13px; color: {SLATE}; margin-bottom: 14px; max-width: 95ch;}}
.card {{ background: {PAPER2}; border: 1px solid {LINE}; border-radius: 6px; padding: 18px 20px; }}
.footnote {{ font-size: 12px; color: {SLATE}; }}
.pill {{
    display:inline-block; font-family:'IBM Plex Mono',monospace; font-size:10.5px;
    background: {PAPER2}; border:1px solid {LINE}; color:{SLATE}; padding:3px 10px; border-radius:14px; margin: 2px 4px 2px 0;
}}
hr.divider {{ border: none; border-top: 1px solid {LINE}; margin: 22px 0; }}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------- DATA LOAD ---
@st.cache_data
def load_data():
    return pd.read_parquet("data/water_points.parquet")

df = load_data()


# ------------------------------------------------------------- SIDEBAR -----
st.sidebar.markdown("### 💧 Water ATM Atlas")
st.sidebar.markdown("<span style='font-family:IBM Plex Mono,monospace;font-size:11px;color:#9FB6B2;'>FILTERS APPLY ACROSS ALL TABS</span>", unsafe_allow_html=True)
st.sidebar.markdown("---")

states = st.sidebar.multiselect("State / UT", sorted(df["State_Name"].unique()), default=[])
sources = st.sidebar.multiselect("Water source tag", sorted(df["Water_Source"].unique()), default=[])
owners = st.sidebar.multiselect("Ownership type", sorted(df["Ownership_Type"].unique()), default=[])
flagged_only = st.sidebar.checkbox("Flagged points only", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<span style='font-family:IBM Plex Mono,monospace;font-size:10.5px;color:#9FB6B2;line-height:1.5;'>"
    "No agency in India publishes a national Water ATM registry. This is OSM-tagged "
    "drinking-water infrastructure cross-checked against news coverage — a research "
    "signal, not an official census. See the Methodology tab."
    "</span>", unsafe_allow_html=True,
)

filtered = df.copy()
if states:
    filtered = filtered[filtered["State_Name"].isin(states)]
if sources:
    filtered = filtered[filtered["Water_Source"].isin(sources)]
if owners:
    filtered = filtered[filtered["Ownership_Type"].isin(owners)]
if flagged_only:
    filtered = filtered[filtered["Flagged"]]

total = len(filtered)
n_states = filtered["State_Name"].nunique()
n_districts = filtered["District_Name"].nunique()
n_flagged = int(filtered["Flagged"].sum())
completeness = filtered["data_completeness_pct"].mean() if total else 0

csv_bytes = filtered.drop(columns=["osm_url", "news_url"], errors="ignore").to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    "⬇ Download filtered data (CSV)", data=csv_bytes,
    file_name="water_atm_filtered.csv", mime="text/csv", width="stretch",
)


# ---------------------------------------------------------------- MASTHEAD -
st.markdown(f"""
<div class="masthead">
  <div class="masthead__row">
    <div>
      <div class="eyebrow">FIELD SURVEY LOG &nbsp;·&nbsp; DRINKING WATER INFRASTRUCTURE &nbsp;·&nbsp; INDIA</div>
      <h1>Water ATM Downtime Atlas</h1>
      <p>A working picture of India's drinking-water points, built from OpenStreetMap
      contributions and cross-checked against live news coverage for signs of failure —
      because no government agency publishes this as a single dataset.</p>
    </div>
    <div class="masthead__badge"><b>{total:,}</b>points in view</div>
  </div>
</div>
""", unsafe_allow_html=True)

tab_overview, tab_map, tab_analytics, tab_flagged, tab_about = st.tabs(
    ["🏠 Overview", "🗺️ Survey Map", "📊 Analytics", "🚩 Flagged Reports", "📘 Methodology"]
)


# ================================================================ OVERVIEW =
with tab_overview:
    k1, k2, k3, k4, k5 = st.columns(5)
    for col, val, label, flag in [
        (k1, f"{total:,}", "mapped points shown", False),
        (k2, f"{n_states}", "states / UTs", False),
        (k3, f"{n_districts}", "districts", False),
        (k4, f"{n_flagged}", "flagged signals", True),
        (k5, f"{completeness:.1f}%", "avg. field completeness", False),
    ]:
        cls = "kpi-value kpi-value--flag" if flag else "kpi-value"
        col.markdown(f"""<div class="kpi-card"><div class="{cls}">{val}</div>
            <div class="kpi-label">{label}</div></div>""", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    oc1, oc2 = st.columns([1.4, 1])
    with oc1:
        st.markdown('<div class="section-title">Where the record is thickest</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-hint">Top 10 states by mapped point count in the current filter.</div>', unsafe_allow_html=True)
        top_states = filtered["State_Name"].value_counts().head(10)
        fig = go.Figure(go.Bar(
            x=top_states.values, y=top_states.index, orientation="h", marker_color=TEAL,
        ))
        fig.update_layout(height=340, margin=dict(l=0, r=10, t=6, b=6),
                           plot_bgcolor=PAPER2, paper_bgcolor=PAPER2,
                           yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
                           font=dict(family="IBM Plex Mono, monospace", size=11, color=SLATE))
        st.plotly_chart(fig, width="stretch")

    with oc2:
        st.markdown('<div class="section-title">At a glance</div>', unsafe_allow_html=True)
        top3 = filtered["State_Name"].value_counts().head(3)
        top_state_txt = ", ".join(f"{s} ({c:,})" for s, c in top3.items()) if len(top3) else "—"
        most_common_source = filtered["Water_Source"].value_counts().idxmax() if total else "—"
        flag_rate = (n_flagged / total * 100) if total else 0
        st.markdown(f"""
        <div class="card">
          <p class="footnote">
          <b>Leading states:</b> {top_state_txt}<br><br>
          <b>Most common source tag:</b> {most_common_source.replace('_',' ')}<br><br>
          <b>Flag rate in current view:</b> {flag_rate:.2f}% of points carry a news-derived non-functional signal<br><br>
          <b>Reading tip:</b> a high point count for a state means OSM mapping is dense there —
          it is not a proxy for water access quality. See Methodology for why.
          </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        for label, val in [("Public ownership", f"{(filtered['Ownership_Type']=='Public').mean()*100:.1f}%" if total else "—"),
                            ("Tagged as wells", f"{(filtered['Water_Source']=='water_well').mean()*100:.1f}%" if total else "—")]:
            st.markdown(f"<span class='pill'>{label}: {val}</span>", unsafe_allow_html=True)


# ============================================================== MAP EXPLORER
with tab_map:
    st.markdown('<div class="section-title">Survey Map</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-hint">Amber pins are points a news article suggests may be '
        'non-functional. Teal pins carry no failure signal — that means "no bad news found," '
        'not "confirmed working." Filters in the sidebar apply here.</div>', unsafe_allow_html=True
    )

    if total == 0:
        st.warning("No points match the current filters.")
    else:
        if total > 8000:
            st.caption(f"Rendering all {total:,} filtered points — clustering keeps this readable, "
                       "but narrow the filters on the left for a snappier map.")

        @st.cache_data(show_spinner=False)
        def build_leaflet_map(states_sel, sources_sel, owners_sel, flagged_only_sel) -> str:
            """Self-contained Leaflet + MarkerCluster map. Cached on filter selection
            (not the dataframe) so revisiting a filter combo is instant."""
            map_df = df.copy()
            if states_sel:
                map_df = map_df[map_df["State_Name"].isin(states_sel)]
            if sources_sel:
                map_df = map_df[map_df["Water_Source"].isin(sources_sel)]
            if owners_sel:
                map_df = map_df[map_df["Ownership_Type"].isin(owners_sel)]
            if flagged_only_sel:
                map_df = map_df[map_df["Flagged"]]

            records = []
            for r in map_df.itertuples(index=False):
                link = r.news_url if isinstance(r.news_url, str) and r.news_url else r.osm_url
                records.append({
                    "lat": r.Latitude, "lon": r.Longitude, "f": bool(r.Flagged),
                    "st": r.State_Name,
                    "d": r.District_Name if pd.notna(r.District_Name) else None,
                    "v": r.Village_City_Name if pd.notna(r.Village_City_Name) else None,
                    "src": r.Water_Source, "own": r.Ownership_Type, "url": link,
                })
            data_json = json.dumps(records, separators=(",", ":"))

            return f"""
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.Default.css">
            <style>
              html, body {{ margin:0; padding:0; }}
              #map {{ height: 560px; width: 100%; border-radius: 4px; }}
              .wa-pin {{ border-radius: 50% 50% 50% 0; transform: rotate(-45deg); display:block; }}
              .wa-pin--teal {{ background: #2F9C8F; border: 2px solid #0C2124; }}
              .wa-pin--amber {{ background: #E08F3C; border: 2px solid #0C2124; }}
              .leaflet-popup-content {{ font-family: Inter, sans-serif; font-size: 13px; }}
            </style>
            <div id="map"></div>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.min.js"></script>
            <script>
              const points = {data_json};
              const map = L.map('map', {{ preferCanvas: true }}).setView([22.9, 79.5], 4);
              L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                attribution: '&copy; OpenStreetMap &copy; CARTO', maxZoom: 18,
              }}).addTo(map);

              const cluster = L.markerClusterGroup({{
                maxClusterRadius: 45,
                iconCreateFunction: function(c) {{
                  const markers = c.getAllChildMarkers();
                  const nFlag = markers.filter(m => m.options.flagged).length;
                  const size = markers.length > 500 ? 44 : markers.length > 50 ? 36 : 28;
                  const color = nFlag > 0 ? '#E08F3C' : '#2F9C8F';
                  return L.divIcon({{
                    html: `<div style="background:${{color}};width:${{size}}px;height:${{size}}px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#0C2124;font-family:'IBM Plex Mono',monospace;font-weight:600;font-size:11px;border:2px solid #0C2124;opacity:0.92;">${{markers.length}}</div>`,
                    className: '', iconSize: [size, size],
                  }});
                }}
              }});

              function icon(flag) {{
                return L.divIcon({{
                  className: '',
                  html: `<span class="wa-pin ${{flag ? 'wa-pin--amber' : 'wa-pin--teal'}}" style="width:14px;height:14px;"></span>`,
                  iconSize: [14, 14], iconAnchor: [7, 14],
                }});
              }}

              points.forEach(p => {{
                const m = L.marker([p.lat, p.lon], {{ icon: icon(p.f), flagged: p.f }});
                m.bindPopup(`
                  <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4B5A5A;text-transform:uppercase;">${{p.f ? '⚠ Flagged by news signal' : 'No failure signal found'}}</div>
                  <div style="font-weight:600;margin:4px 0 2px;">${{p.v ? p.v + ', ' : ''}}${{p.d || 'Unknown district'}}</div>
                  <div style="color:#4B5A5A;margin-bottom:6px;">${{p.st}}</div>
                  <div style="font-size:12px;color:#4B5A5A;">Source: ${{p.src}} &middot; Owner: ${{p.own}}</div>
                  ${{p.url ? `<a href="${{p.url}}" target="_blank" rel="noopener" style="font-size:12px;color:#155E5A;">View source →</a>` : ''}}
                `);
                cluster.addLayer(m);
              }});
              map.addLayer(cluster);
              if (points.length > 0) {{
                try {{ map.fitBounds(cluster.getBounds().pad(0.1)); }} catch (e) {{}}
              }}
            </script>
            """

        map_html = build_leaflet_map(tuple(states), tuple(sources), tuple(owners), flagged_only)
        st.iframe(map_html, height=575)

        legend_col1, legend_col2 = st.columns([1, 4])
        legend_col1.markdown(
            f"<span style='color:{TEAL_BRIGHT};'>●</span> No signal &nbsp;&nbsp; "
            f"<span style='color:{AMBER_BRIGHT};'>●</span> Flagged",
            unsafe_allow_html=True,
        )


# =================================================================ANALYTICS=
with tab_analytics:
    st.markdown('<div class="section-title">Infrastructure Breakdown</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-hint">All charts reflect the sidebar filters currently applied.</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.3, 1, 1])
    with c1:
        st.markdown("**Top Districts**")
        dist_counts = (filtered.dropna(subset=["District_Name"])
                       .groupby(["State_Name", "District_Name"]).size()
                       .reset_index(name="count").sort_values("count", ascending=False).head(12))
        if not dist_counts.empty:
            fig = go.Figure(go.Bar(
                x=dist_counts["count"], y=dist_counts["District_Name"] + " (" + dist_counts["State_Name"] + ")",
                orientation="h", marker_color=TEAL,
            ))
            fig.update_layout(height=380, margin=dict(l=0, r=10, t=10, b=10),
                               plot_bgcolor=PAPER2, paper_bgcolor=PAPER2,
                               yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
                               font=dict(family="IBM Plex Mono, monospace", size=11, color=SLATE))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No district-level data for current filters.")

    with c2:
        st.markdown("**Water Source Tags**")
        src_counts = filtered["Water_Source"].value_counts().head(6)
        fig = go.Figure(go.Pie(labels=src_counts.index, values=src_counts.values, hole=0.62,
                                marker_colors=[TEAL, TEAL_BRIGHT, "#5FBCAE", AMBER, AMBER_BRIGHT, "#8FA8A4"]))
        fig.update_layout(height=330, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor=PAPER2,
                           showlegend=True, legend=dict(font=dict(size=10)))
        st.plotly_chart(fig, width="stretch")

    with c3:
        st.markdown("**Ownership Type**")
        own_counts = filtered["Ownership_Type"].value_counts().head(5)
        fig = go.Figure(go.Pie(labels=own_counts.index, values=own_counts.values, hole=0.62,
                                marker_colors=[TEAL, TEAL_BRIGHT, "#5FBCAE", AMBER, AMBER_BRIGHT]))
        fig.update_layout(height=330, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor=PAPER2,
                           showlegend=True, legend=dict(font=dict(size=10)))
        st.plotly_chart(fig, width="stretch")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Mapped Points by State</div>', unsafe_allow_html=True)
    state_counts = filtered["State_Name"].value_counts().head(15)
    fig = go.Figure(go.Bar(x=state_counts.index, y=state_counts.values, marker_color=TEAL))
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor=PAPER2, paper_bgcolor=PAPER2,
                       font=dict(family="IBM Plex Mono, monospace", size=11, color=SLATE))
    st.plotly_chart(fig, width="stretch")

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Drill into a state</div>', unsafe_allow_html=True)
    drill_states = sorted(filtered["State_Name"].unique())
    if drill_states:
        pick = st.selectbox("Choose a state to see its district breakdown", drill_states)
        state_df = filtered[filtered["State_Name"] == pick]
        d_counts = (state_df.dropna(subset=["District_Name"])["District_Name"]
                    .value_counts().head(15))
        if not d_counts.empty:
            fig = go.Figure(go.Bar(x=d_counts.values, y=d_counts.index, orientation="h", marker_color=TEAL_BRIGHT))
            fig.update_layout(height=360, margin=dict(l=0, r=10, t=10, b=10),
                               plot_bgcolor=PAPER2, paper_bgcolor=PAPER2,
                               yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
                               font=dict(family="IBM Plex Mono, monospace", size=11, color=SLATE))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info(f"No district-level detail recorded for {pick} in the current filter.")


# ================================================================ FLAGGED ==
with tab_flagged:
    st.markdown('<div class="section-title">Flagged Field Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-hint">Every row is a specific water point where a matched '
                'news article used language suggesting it may be broken, dry, or abandoned. '
                'Click through and verify — this is a lead list, not a finding.</div>',
                unsafe_allow_html=True)

    flagged_df = filtered[filtered["Flagged"]].copy()
    search = st.text_input("Search state, district, or village", "")
    if search:
        mask = (flagged_df["State_Name"].str.contains(search, case=False, na=False) |
                flagged_df["District_Name"].str.contains(search, case=False, na=False) |
                flagged_df["Village_City_Name"].str.contains(search, case=False, na=False))
        flagged_df = flagged_df[mask]

    if flagged_df.empty:
        st.info("No flagged points match the current filters/search.")
    else:
        flagged_df["Link"] = flagged_df["news_url"].where(
            flagged_df["news_url"].str.len() > 0, flagged_df["osm_url"]
        )
        st.dataframe(
            flagged_df[["State_Name", "District_Name", "Village_City_Name", "Latitude", "Longitude", "Link"]],
            column_config={
                "State_Name": "State", "District_Name": "District",
                "Village_City_Name": "Village / City",
                "Link": st.column_config.LinkColumn("Source", display_text="View →"),
            },
            hide_index=True, width="stretch", height=420,
        )
        st.caption(f"{len(flagged_df):,} flagged point(s) shown.")


# ================================================================== ABOUT ==
with tab_about:
    st.markdown('<div class="section-title">Methodology & Honest Limitations</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="card">
    <p class="footnote">
    <b>What this is.</b> {len(df):,} drinking-water infrastructure points across India
    (wells, taps, water points, storage tanks, RO/vending units) tagged in
    OpenStreetMap, cross-checked against Google News coverage for language suggesting
    a point is non-functional.<br><br>

    <b>What this is not.</b> India has no public, centralized Water ATM registry —
    installation numbers get announced by individual schemes, Smart City programs,
    CSR initiatives, and vendors, but nothing tracks them together. This dashboard is
    the closest assemblable substitute from open data, not an official census.<br><br>

    <b>Why some states dominate.</b> Maharashtra and Kerala together account for a large
    share of points here because OpenStreetMap contributor activity is denser in those
    states — not because water infrastructure is denser there. Treat state-level counts
    as a map of <i>where the open record is thick</i>, not where service is best or worst.<br><br>

    <b>How "flagged" is determined.</b> A rule-based keyword match against news article
    titles/summaries (terms like "non-functional," "defunct," "vandalised," "not working")
    linked back to the nearest OSM point by location/name proximity. This is a lead
    list for manual verification, not a confirmed operational status — false positives
    and false negatives are both possible.<br><br>

    <b>Field completeness.</b> Most granular operational fields in the original schema
    (installation year, AMC status, maintenance agency, vendor) are not publicly
    disclosed anywhere and are marked <code>Unknown</code> rather than guessed. The
    completeness percentage shown reflects how many of the requested fields could
    actually be populated from public sources.
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Data provenance</div>', unsafe_allow_html=True)
    mc1, mc2 = st.columns(2)
    mc1.markdown("""
    <div class="card"><p class="footnote">
    <b>Primary source:</b> OpenStreetMap (openstreetmap.org) drinking-water tags,
    queried via the Overpass API.<br><br>
    <b>Signal source:</b> Google News RSS, keyword-matched and geo-linked to the
    nearest OSM point.
    </p></div>
    """, unsafe_allow_html=True)
    mc2.markdown("""
    <div class="card"><p class="footnote">
    <b>Update path:</b> re-run <code>build_data.py</code> against a refreshed export
    to regenerate <code>data/water_points.parquet</code> — no code changes needed.<br><br>
    <b>Repo:</b> this dashboard's source lives alongside its data for full reproducibility.
    </p></div>
    """, unsafe_allow_html=True)
