import json
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

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
BORDER = "#C9C6B6"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background-color: {PAPER}; }}
#MainMenu, footer {{ visibility: hidden; }}
.block-container {{ padding-top: 1.2rem; max-width: 1300px; }}

[data-testid="stSidebar"] {{ background-color: {INK}; }}
[data-testid="stSidebar"] * {{ color: #EAF3F1 !important; }}
[data-testid="stSidebar"] .stSlider label, [data-testid="stSidebar"] label {{ color: #9FB6B2 !important; }}

/* Sidebar multiselect / select boxes: lighter fill so they read as inputs, not blank boxes */
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background-color: #16383B !important;
    border: 1px solid #2A5B58 !important;
    color: #EAF3F1 !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] input {{
    color: #EAF3F1 !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] div[aria-live] {{
    color: #9FB6B2 !important;
}}
[data-testid="stSidebar"] [data-baseweb="tag"] {{
    background-color: {TEAL_BRIGHT} !important; color: {INK} !important;
}}
[data-testid="stSidebar"] svg {{ fill: #9FB6B2 !important; }}

/* ---------- Top navbar ---------- */
.topbar {{
    display:flex; align-items:center; justify-content:space-between;
    background: {INK}; color:#EAF3F1; padding: 16px 28px; border-radius: 8px;
    margin-bottom: 14px;
}}
.topbar-brand {{ display:flex; align-items:center; gap:12px; }}
.topbar-logo {{
    width:38px; height:38px; border-radius:8px; background:{TEAL_BRIGHT};
    display:flex; align-items:center; justify-content:center; font-size:19px;
}}
.topbar-title {{ font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:19px; color:#fff; line-height:1.1; }}
.topbar-sub {{ font-family:'IBM Plex Mono',monospace; font-size:10.5px; letter-spacing:.08em;
    text-transform:uppercase; color:{TEAL_BRIGHT}; }}
.topbar-status {{ display:flex; align-items:center; gap:8px; font-family:'IBM Plex Mono',monospace;
    font-size:11px; color:#9FB6B2; }}
.dot {{ width:7px; height:7px; border-radius:50%; background:{TEAL_BRIGHT}; box-shadow:0 0 0 3px rgba(47,156,143,0.25); }}

/* ---------- Hero ---------- */
.hero {{
    background: linear-gradient(135deg, {INK} 0%, #123638 100%); color: #EAF3F1;
    padding: 30px 34px 24px; border-radius: 8px; margin-bottom: 18px;
}}
.hero .eyebrow {{
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: .12em;
    color: {TEAL_BRIGHT}; text-transform: uppercase; margin-bottom: 10px;
}}
.hero h1 {{
    font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 36px;
    margin: 0 0 10px; line-height: 1.05; color: #fff;
}}
.hero p {{ color: #C3D6D2; max-width: 760px; font-size: 14px; margin:0; }}

/* ---------- Cards ---------- */
.kpi-card {{
    background: {PAPER2}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 14px 16px; text-align:left; transition: border-color .15s ease;
}}
.kpi-card:hover {{ border-color: {TEAL_BRIGHT}; }}
.kpi-value {{ font-family: 'Space Grotesk', sans-serif; font-weight:700; font-size: 27px; color: {INK}; }}
.kpi-value--flag {{ color: {AMBER}; }}
.kpi-label {{ font-family: 'IBM Plex Mono', monospace; font-size: 10px; text-transform: uppercase;
    letter-spacing: .05em; color: {SLATE}; margin-top:2px; }}

.info-card {{
    background:{PAPER2}; border:1px solid {BORDER}; border-left:4px solid {TEAL_BRIGHT};
    border-radius:6px; padding:16px 18px; height:100%;
}}
.info-card .tag {{ font-family:'IBM Plex Mono',monospace; font-size:10px; text-transform:uppercase;
    letter-spacing:.06em; color:{TEAL}; margin-bottom:6px; }}
.info-card .big {{ font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:20px; color:{INK}; }}
.info-card .desc {{ font-size:12.5px; color:{SLATE}; margin-top:4px; }}

.step-card {{
    background:{PAPER2}; border:1px solid {BORDER}; border-radius:8px; padding:16px 18px;
    display:flex; gap:14px; align-items:flex-start; margin-bottom:10px;
}}
.step-num {{
    font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:16px; color:#fff;
    background:{TEAL}; width:30px; height:30px; min-width:30px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
}}
.step-title {{ font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:14.5px; color:{INK}; }}
.step-desc {{ font-size:12.5px; color:{SLATE}; margin-top:2px; }}

.badge {{
    display:inline-block; font-family:'IBM Plex Mono',monospace; font-size:10.5px;
    background:{INK}; color:#EAF3F1; padding:5px 11px; border-radius:20px; margin:0 6px 6px 0;
}}

.section-title {{ font-family: 'Space Grotesk', sans-serif; font-weight:700; font-size:18px; color:{INK}; margin: 6px 0 2px;}}
.section-hint {{ font-size: 12.5px; color: {SLATE}; margin-bottom: 10px; max-width: 95ch;}}
.footnote {{ font-size: 12px; color: {SLATE}; border-top: 1px solid {BORDER}; padding-top: 14px; margin-top: 10px;}}

.footer {{
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;
    border-top: 1px solid {BORDER}; margin-top: 26px; padding-top: 16px; padding-bottom: 4px;
    font-family:'IBM Plex Mono',monospace; font-size:12px; font-weight:500; color:{INK};
}}
.footer a {{ color:{TEAL}; font-weight:600; text-decoration:none; }}
.footer a:hover {{ text-decoration:underline; }}

/* ---------- Tabs as a website nav ---------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px; border-bottom: 2px solid {BORDER}; margin-bottom: 6px;
}}
.stTabs [data-baseweb="tab"] {{
    height: 42px; padding: 0 18px; background-color: transparent;
    font-family:'Space Grotesk',sans-serif; font-weight:600; font-size:13.5px;
    color:{SLATE}; border-radius: 8px 8px 0 0;
}}
.stTabs [aria-selected="true"] {{
    background-color: {INK} !important; color: #EAF3F1 !important;
}}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------- DATA LOAD ---
@st.cache_data
def load_data():
    df = pd.read_parquet("data/water_points.parquet")
    return df

df = load_data()


# --------------------------------------------------------- LEAFLET MAP -----
@st.cache_data(show_spinner=False)
def build_leaflet_map(states_sel, sources_sel, owners_sel, flagged_only_sel) -> str:
    """Builds a self-contained Leaflet + MarkerCluster map as an HTML string.
    Cached on the filter selection (not the dataframe) so re-selecting a
    filter combination you've already viewed is instant instead of
    re-serializing tens of thousands of points. This exists because pydeck
    renders raw overlapping dots at country zoom with 36k points; Leaflet's
    clustering reads far better at that scale and matches the original
    static-dashboard map exactly."""
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
      #map {{ height: 600px; width: 100%; border-radius: 8px; }}
      .wa-pin {{ border-radius: 50% 50% 50% 0; transform: rotate(-45deg); display:block; }}
      .wa-pin--teal {{ background: #2F9C8F; border: 2px solid #0C2124; }}
      .wa-pin--amber {{ background: #E08F3C; border: 2px solid #0C2124; }}
      .leaflet-popup-content {{ font-family: Inter, sans-serif; font-size: 13px; }}
      .map-legend {{
        position:absolute; bottom:14px; left:14px; z-index:500; background:rgba(12,33,36,0.92);
        color:#EAF3F1; padding:10px 14px; border-radius:8px; font-family:'IBM Plex Mono',monospace;
        font-size:11px; line-height:1.9;
      }}
      .swatch {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:7px; }}
    </style>
    <div style="position:relative;">
      <div id="map"></div>
      <div class="map-legend">
        <div><span class="swatch" style="background:#E08F3C;"></span>Flagged by news signal</div>
        <div><span class="swatch" style="background:#2F9C8F;"></span>No failure signal found</div>
      </div>
    </div>
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


# ------------------------------------------------------------- SIDEBAR -----
st.sidebar.markdown(
    """
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">
        <div style="width:34px;height:34px;border-radius:8px;background:#2F9C8F;
             display:flex;align-items:center;justify-content:center;font-size:17px;">💧</div>
        <div>
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:15px;color:#fff;">
                Downtime Atlas
            </div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:9.5px;letter-spacing:.06em;
                 text-transform:uppercase;color:#2F9C8F;">India · Water Infra</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### Filters")

states = st.sidebar.multiselect(
    "State / UT", sorted(df["State_Name"].unique()), default=[]
)
sources = st.sidebar.multiselect(
    "Water source tag", sorted(df["Water_Source"].unique()), default=[]
)
owners = st.sidebar.multiselect(
    "Ownership type", sorted(df["Ownership_Type"].unique()), default=[]
)
flagged_only = st.sidebar.checkbox("Flagged points only", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<span style='font-family:IBM Plex Mono,monospace;font-size:11px;'>"
    "No agency in India publishes a national Water ATM registry. This dataset "
    "is OSM-tagged drinking-water infrastructure cross-checked against news "
    "coverage — a research signal, not an official census."
    "</span>",
    unsafe_allow_html=True,
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


# ----------------------------------------------------------------- TOPBAR --
st.markdown(f"""
<div class="topbar">
  <div class="topbar-brand">
    <div class="topbar-logo">💧</div>
    <div>
      <div class="topbar-title">Water ATM Downtime Atlas</div>
      <div class="topbar-sub">Field Survey Log · India</div>
    </div>
  </div>
  <div class="topbar-status"><span class="dot"></span>{total:,} points in current view</div>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------------------- NAV TABS --
tab_overview, tab_map, tab_analytics, tab_flagged, tab_method = st.tabs(
    ["🏠  Overview", "🗺️  Survey Map", "📊  Analytics", "🚩  Flagged Reports", "📖  Methodology"]
)


# ================================================================ OVERVIEW =
with tab_overview:
    st.markdown(f"""
    <div class="hero">
      <div class="eyebrow">FIELD SURVEY LOG &nbsp;·&nbsp; DRINKING WATER INFRASTRUCTURE &nbsp;·&nbsp; INDIA</div>
      <h1>Every dot is a drinking-water point, checked for signs of failure.</h1>
      <p>Mapped from OpenStreetMap contributions and cross-checked against live news coverage.
      Use the filters on the left to narrow the map, charts, and flagged-report table across every
      tab — they all stay in sync.</p>
    </div>
    """, unsafe_allow_html=True)

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

    st.write("")
    st.markdown('<div class="section-title">At a Glance</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-hint">Quick highlights from the current filter selection.</div>',
                unsafe_allow_html=True)

    if total > 0:
        top_state = filtered["State_Name"].value_counts().idxmax()
        top_state_n = filtered["State_Name"].value_counts().max()
        top_source = filtered["Water_Source"].value_counts().idxmax()
        top_source_n = filtered["Water_Source"].value_counts().max()
        flag_rate = (n_flagged / total * 100) if total else 0

        i1, i2, i3 = st.columns(3)
        with i1:
            st.markdown(f"""<div class="info-card"><div class="tag">Leading State</div>
                <div class="big">{top_state}</div>
                <div class="desc">{top_state_n:,} mapped points — the densest OSM coverage in this view.</div>
                </div>""", unsafe_allow_html=True)
        with i2:
            st.markdown(f"""<div class="info-card"><div class="tag">Most Common Source</div>
                <div class="big">{top_source}</div>
                <div class="desc">{top_source_n:,} points tagged with this water-source type.</div>
                </div>""", unsafe_allow_html=True)
        with i3:
            st.markdown(f"""<div class="info-card"><div class="tag">Flag Rate</div>
                <div class="big">{flag_rate:.1f}%</div>
                <div class="desc">Share of points with a matched news signal suggesting failure.</div>
                </div>""", unsafe_allow_html=True)

        st.write("")
        st.markdown('<div class="section-title">Top States, Preview</div>', unsafe_allow_html=True)
        preview_counts = filtered["State_Name"].value_counts().head(8)
        fig = go.Figure(go.Bar(
            x=preview_counts.values, y=preview_counts.index, orientation="h", marker_color=TEAL_BRIGHT,
        ))
        fig.update_layout(
            height=300, margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor=PAPER2, paper_bgcolor=PAPER2,
            yaxis=dict(autorange="reversed", tickfont=dict(size=11), automargin=True),
            font=dict(family="IBM Plex Mono, monospace", size=11, color=SLATE),
        )
        st.plotly_chart(fig, width="stretch")
        st.caption("Open the **Survey Map** tab for the full interactive map, or **Analytics** for the complete chart set.")
    else:
        st.warning("No points match the current filters.")


# ================================================================ MAP ======
with tab_map:
    st.markdown('<div class="section-title">Survey Map</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-hint">Amber pins are points a news article suggests may be '
        'non-functional. Teal pins carry no failure signal — that means "no bad news found," '
        'not "confirmed working." Clusters show counts; zoom in to break them apart.</div>',
        unsafe_allow_html=True
    )

    if total == 0:
        st.warning("No points match the current filters.")
    else:
        if total > 8000:
            st.caption(
                f"Rendering all {total:,} filtered points — clustering keeps this readable, "
                "but narrow the filters on the left for a snappier map."
            )
        map_html = build_leaflet_map(tuple(states), tuple(sources), tuple(owners), flagged_only)
        components.html(map_html, height=615, scrolling=False)


# ================================================================ ANALYTICS =
with tab_analytics:
    st.markdown('<div class="section-title">Distribution &amp; Composition</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-hint">All charts react to the sidebar filters.</div>',
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1.3, 1, 1])

    with c1:
        st.markdown('<div class="section-title" style="font-size:15px;">Top Districts</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-hint">By mapped point count — reflects OSM contributor '
                    'density as much as real infrastructure.</div>', unsafe_allow_html=True)
        dist_counts = (filtered.dropna(subset=["District_Name"])
                       .groupby(["State_Name", "District_Name"]).size()
                       .reset_index(name="count").sort_values("count", ascending=False).head(12))
        if not dist_counts.empty:
            fig = go.Figure(go.Bar(
                x=dist_counts["count"], y=dist_counts["District_Name"] + " (" + dist_counts["State_Name"] + ")",
                orientation="h", marker_color=TEAL,
            ))
            fig.update_layout(
                height=380, margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor=PAPER2, paper_bgcolor=PAPER2,
                yaxis=dict(autorange="reversed", tickfont=dict(size=11), automargin=True),
                font=dict(family="IBM Plex Mono, monospace", size=11, color=SLATE),
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No district-level data for current filters.")

    with c2:
        st.markdown('<div class="section-title" style="font-size:15px;">Water Source Tags</div>', unsafe_allow_html=True)
        src_counts = filtered["Water_Source"].value_counts().head(6)
        fig = go.Figure(go.Pie(
            labels=src_counts.index, values=src_counts.values, hole=0.62,
            marker_colors=[TEAL, TEAL_BRIGHT, "#5FBCAE", AMBER, AMBER_BRIGHT, "#8FA8A4"],
        ))
        fig.update_layout(height=330, margin=dict(l=0, r=0, t=10, b=0),
                           paper_bgcolor=PAPER2, showlegend=True,
                           legend=dict(font=dict(size=10)))
        st.plotly_chart(fig, width="stretch")

    with c3:
        st.markdown('<div class="section-title" style="font-size:15px;">Ownership Type</div>', unsafe_allow_html=True)
        own_counts = filtered["Ownership_Type"].value_counts().head(5)
        fig = go.Figure(go.Pie(
            labels=own_counts.index, values=own_counts.values, hole=0.62,
            marker_colors=[TEAL, TEAL_BRIGHT, "#5FBCAE", AMBER, AMBER_BRIGHT],
        ))
        fig.update_layout(height=330, margin=dict(l=0, r=0, t=10, b=0),
                           paper_bgcolor=PAPER2, showlegend=True,
                           legend=dict(font=dict(size=10)))
        st.plotly_chart(fig, width="stretch")

    st.write("")
    st.markdown('<div class="section-title">Mapped Points by State</div>', unsafe_allow_html=True)
    state_counts = filtered["State_Name"].value_counts().head(15)
    fig = go.Figure(go.Bar(x=state_counts.index, y=state_counts.values, marker_color=TEAL))
    fig.update_layout(
        height=320, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor=PAPER2, paper_bgcolor=PAPER2,
        font=dict(family="IBM Plex Mono, monospace", size=11, color=SLATE),
    )
    st.plotly_chart(fig, width="stretch")

    st.write("")
    a1, a2 = st.columns(2)
    with a1:
        st.markdown('<div class="section-title" style="font-size:15px;">Field Completeness Spread</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-hint">How complete each record\'s fields are, across the current selection.</div>',
                    unsafe_allow_html=True)
        if total > 0:
            fig = go.Figure(go.Histogram(
                x=filtered["data_completeness_pct"], nbinsx=20, marker_color=TEAL_BRIGHT,
            ))
            fig.update_layout(
                height=300, margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor=PAPER2, paper_bgcolor=PAPER2,
                xaxis_title="Completeness %", yaxis_title="Points",
                font=dict(family="IBM Plex Mono, monospace", size=10.5, color=SLATE),
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No data for current filters.")

    with a2:
        st.markdown('<div class="section-title" style="font-size:15px;">Flagged Share by Ownership</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-hint">Which ownership types carry the largest share of flagged signals.</div>',
                    unsafe_allow_html=True)
        if total > 0:
            grp = filtered.groupby("Ownership_Type")["Flagged"].agg(["sum", "count"]).reset_index()
            grp["rate"] = (grp["sum"] / grp["count"] * 100).round(1)
            grp = grp.sort_values("rate", ascending=False).head(8)
            fig = go.Figure(go.Bar(
                x=grp["rate"], y=grp["Ownership_Type"], orientation="h", marker_color=AMBER,
            ))
            fig.update_layout(
                height=300, margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor=PAPER2, paper_bgcolor=PAPER2,
                xaxis_title="Flagged %",
                yaxis=dict(autorange="reversed", tickfont=dict(size=11), automargin=True),
                font=dict(family="IBM Plex Mono, monospace", size=10.5, color=SLATE),
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No data for current filters.")


# ================================================================ FLAGGED ==
with tab_flagged:
    st.markdown('<div class="section-title">Flagged Field Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-hint">Every row is a specific water point where a matched '
                'news article used language suggesting it may be broken, dry, or abandoned. '
                'Click through and verify — this is a lead list, not a finding.</div>',
                unsafe_allow_html=True)

    flagged_df = filtered[filtered["Flagged"]].copy()

    search = st.text_input("Search by state, district, or village", "", placeholder="e.g. Maharashtra, Pune, Wardha…")
    if search:
        mask = (
            flagged_df["State_Name"].str.contains(search, case=False, na=False)
            | flagged_df["District_Name"].str.contains(search, case=False, na=False)
            | flagged_df["Village_City_Name"].str.contains(search, case=False, na=False)
        )
        flagged_df = flagged_df[mask]

    if flagged_df.empty:
        st.info("No flagged points match the current filters.")
    else:
        flagged_df["Link"] = flagged_df["news_url"].where(
            flagged_df["news_url"].str.len() > 0, flagged_df["osm_url"]
        )
        display_cols = ["State_Name", "District_Name", "Village_City_Name",
                         "Latitude", "Longitude", "Link"]
        st.caption(f"{len(flagged_df):,} flagged points match your filters and search.")
        st.dataframe(
            flagged_df[display_cols],
            column_config={
                "State_Name": "State",
                "District_Name": "District",
                "Village_City_Name": "Village / City",
                "Link": st.column_config.LinkColumn("Source", display_text="View →"),
            },
            hide_index=True,
            width="stretch",
            height=420,
        )
        st.download_button(
            "⬇ Download flagged report (CSV)",
            data=flagged_df[display_cols].to_csv(index=False).encode("utf-8"),
            file_name="water_atm_flagged_report.csv",
            mime="text/csv",
        )


# ================================================================ METHOD ===
with tab_method:
    st.markdown('<div class="section-title">How This Atlas Was Built</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-hint">A research pipeline stitched together from three public sources — '
                'no official registry exists to pull from directly.</div>', unsafe_allow_html=True)

    steps = [
        ("Collect", "Pulled drinking-water infrastructure tags (wells, taps, RO/vending units, water points) "
                     "from the OpenStreetMap Overpass API across every Indian state and UT."),
        ("Cross-check", "Matched each point against data.gov.in datasets and Google News RSS coverage, "
                         "scanning article text for language suggesting failure, disrepair, or abandonment."),
        ("Correct", "Ran spatial joins against India's official district-boundary shapefiles to fix "
                     "mismatched or missing state/district assignments in the raw tags."),
        ("Deduplicate", "Collapsed overlapping OSM entries and near-duplicate coordinates down to a clean, "
                         "one-row-per-point dataset."),
        ("Publish", "Exported to a Power BI-ready format and this Streamlit atlas, with every point "
                     "tagged for completeness and flag status."),
    ]
    for i, (title, desc) in enumerate(steps, start=1):
        st.markdown(f"""<div class="step-card">
            <div class="step-num">{i}</div>
            <div><div class="step-title">{title}</div><div class="step-desc">{desc}</div></div>
            </div>""", unsafe_allow_html=True)

    st.write("")
    st.markdown('<div class="section-title">Data Sources</div>', unsafe_allow_html=True)
    st.markdown("""
    <span class="badge">OpenStreetMap Overpass API</span>
    <span class="badge">data.gov.in</span>
    <span class="badge">Google News RSS</span>
    <span class="badge">India District Boundaries (spatial join)</span>
    """, unsafe_allow_html=True)

    st.write("")
    st.markdown(f"""
    <div class="footnote">
    <strong>Reading this atlas honestly:</strong> These points are drinking-water infrastructure tagged
    in OpenStreetMap (wells, taps, water points, RO/vending units), not an official Water ATM census —
    India has no such public dataset. Maharashtra and Kerala dominate the counts because volunteer mapping
    is denser there, not because service is denser there. Flagged points come from automated keyword
    matching against news text and require manual verification before any operational decision is made
    on them.
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------------ FOOTER -
st.markdown("""
<div class="footer">
  <div>Water ATM Downtime Atlas — a research signal, not an official census.</div>
  <div>
    Built by Koushik Garg ·
    <a href="https://github.com/koushikgarg11" target="_blank">GitHub</a> ·
    <a href="https://www.linkedin.com" target="_blank">LinkedIn</a>
  </div>
</div>
""", unsafe_allow_html=True)
