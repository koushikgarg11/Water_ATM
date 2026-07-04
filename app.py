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

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

.stApp {{ background-color: {PAPER}; }}
[data-testid="stSidebar"] {{ background-color: {INK}; }}
[data-testid="stSidebar"] * {{ color: #EAF3F1 !important; }}
[data-testid="stSidebar"] .stSlider label, [data-testid="stSidebar"] label {{ color: #9FB6B2 !important; }}

.hero {{
    background: {INK}; color: #EAF3F1; padding: 34px 38px 26px; border-radius: 6px; margin-bottom: 18px;
}}
.hero .eyebrow {{
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: .12em;
    color: {TEAL_BRIGHT}; text-transform: uppercase; margin-bottom: 10px;
}}
.hero h1 {{
    font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 42px;
    margin: 0 0 10px; line-height: 1.02; color: #fff;
}}
.hero p {{ color: #C3D6D2; max-width: 760px; font-size: 14.5px; margin:0; }}

.kpi-card {{
    background: {PAPER2}; border: 1px solid #C9C6B6; border-radius: 5px;
    padding: 14px 16px; text-align:left;
}}
.kpi-value {{ font-family: 'Space Grotesk', sans-serif; font-weight:700; font-size: 28px; color: {INK}; }}
.kpi-value--flag {{ color: {AMBER}; }}
.kpi-label {{ font-family: 'IBM Plex Mono', monospace; font-size: 10.5px; text-transform: uppercase;
    letter-spacing: .05em; color: {SLATE}; margin-top:2px; }}

.section-title {{ font-family: 'Space Grotesk', sans-serif; font-weight:700; font-size:19px; color:{INK}; margin: 4px 0 2px;}}
.section-hint {{ font-size: 13px; color: {SLATE}; margin-bottom: 10px; max-width: 90ch;}}
.footnote {{ font-size: 12px; color: {SLATE}; border-top: 1px solid #C9C6B6; padding-top: 14px; margin-top: 10px;}}
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


# ------------------------------------------------------------- SIDEBAR -----
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


# ------------------------------------------------------------------ HERO ---
st.markdown(f"""
<div class="hero">
  <div class="eyebrow">FIELD SURVEY LOG &nbsp;·&nbsp; DRINKING WATER INFRASTRUCTURE &nbsp;·&nbsp; INDIA</div>
  <h1>Water ATM Downtime Atlas</h1>
  <p>Every dot is a drinking-water point mapped from OpenStreetMap contributions and cross-checked
  against live news coverage for signs of failure. Use the filters on the left to narrow the map,
  charts, and flagged-report table below — they all stay in sync.</p>
</div>
""", unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)
total = len(filtered)
n_states = filtered["State_Name"].nunique()
n_districts = filtered["District_Name"].nunique()
n_flagged = int(filtered["Flagged"].sum())
completeness = filtered["data_completeness_pct"].mean() if total else 0

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


# ------------------------------------------------------------------- MAP ---
st.markdown('<div class="section-title">Survey Map</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-hint">Amber pins are points a news article suggests may be '
    'non-functional. Teal pins carry no failure signal — that means "no bad news found," '
    'not "confirmed working."</div>', unsafe_allow_html=True
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
    components.html(map_html, height=575, scrolling=False)

st.write("")


# -------------------------------------------------------------- CHARTS -----
c1, c2, c3 = st.columns([1.3, 1, 1])

with c1:
    st.markdown('<div class="section-title">Top Districts</div>', unsafe_allow_html=True)
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
            height=380, margin=dict(l=0, r=10, t=10, b=10),
            plot_bgcolor=PAPER2, paper_bgcolor=PAPER2,
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
            font=dict(family="IBM Plex Mono, monospace", size=11, color=SLATE),
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No district-level data for current filters.")

with c2:
    st.markdown('<div class="section-title">Water Source Tags</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="section-title">Ownership Type</div>', unsafe_allow_html=True)
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


# ---------------------------------------------------------- FLAGGED LOG ----
st.write("")
st.markdown('<div class="section-title">Flagged Field Reports</div>', unsafe_allow_html=True)
st.markdown('<div class="section-hint">Every row is a specific water point where a matched '
            'news article used language suggesting it may be broken, dry, or abandoned. '
            'Click through and verify — this is a lead list, not a finding.</div>',
            unsafe_allow_html=True)

flagged_df = filtered[filtered["Flagged"]].copy()
if flagged_df.empty:
    st.info("No flagged points match the current filters.")
else:
    flagged_df["Link"] = flagged_df["news_url"].where(
        flagged_df["news_url"].str.len() > 0, flagged_df["osm_url"]
    )
    display_cols = ["State_Name", "District_Name", "Village_City_Name",
                     "Latitude", "Longitude", "Link"]
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
        height=380,
    )

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
