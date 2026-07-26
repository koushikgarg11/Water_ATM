
import json
import os
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
import hashlib
import secrets
from typing import Dict, Any
from datetime import datetime, timedelta
import re

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


USERS_PATH = Path(__file__).resolve().parent / "users.json"


def load_users() -> Dict[str, Any]:
    if not USERS_PATH.exists():
        return {}
    try:
        return json.loads(USERS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_users(users: Dict[str, Any]) -> None:
    USERS_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    if salt_hex is None:
        salt_hex = secrets.token_hex(16)
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt_hex, dk.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    _, calc = hash_password(password, salt_hex)
    return secrets.compare_digest(calc, hash_hex)


def authenticate(username: str, password: str) -> bool:
    users = load_users()
    if username in users:
        entry = users[username]
        return verify_password(password, entry.get("salt", ""), entry.get("hash", ""))
    # fallback to environment credential for first-time admin access
    # Do not use insecure hardcoded defaults; require both env vars to be set.
    expected_user = os.getenv("WATER_ATM_USERNAME")
    expected_password = os.getenv("WATER_ATM_PASSWORD")
    if expected_user and expected_password:
        return username == expected_user and password == expected_password
    return False


def _is_locked(users: Dict[str, Any], username: str) -> tuple[bool, int]:
    """Return (locked, seconds_remaining) for a user record."""
    entry = users.get(username, {})
    lu = entry.get("locked_until")
    if not lu:
        return False, 0
    try:
        until = datetime.fromisoformat(lu)
    except Exception:
        return False, 0
    now = datetime.utcnow()
    if until > now:
        return True, int((until - now).total_seconds())
    return False, 0


def _record_failed_attempt(users: Dict[str, Any], username: str, limit: int = 5, lock_minutes: int = 15) -> None:
    entry = users.get(username)
    if entry is None:
        return
    fa = int(entry.get("failed_attempts", 0)) + 1
    entry["failed_attempts"] = fa
    if fa >= limit:
        entry["locked_until"] = (datetime.utcnow() + timedelta(minutes=lock_minutes)).isoformat()
        entry["failed_attempts"] = 0
    users[username] = entry
    save_users(users)


def _reset_failed_attempts(users: Dict[str, Any], username: str) -> None:
    entry = users.get(username)
    if not entry:
        return
    entry.pop("failed_attempts", None)
    entry.pop("locked_until", None)
    users[username] = entry
    save_users(users)


def _validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include an uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must include a lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must include a number."
    if not re.search(r"[^A-Za-z0-9]", password):
        return False, "Password must include a special character."
    return True, ""


def register_user(username: str, password: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "Username and password are required."
    users = load_users()
    if username in users:
        return False, "Username already exists."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    salt, h = hash_password(password)
    users[username] = {"salt": salt, "hash": h}
    save_users(users)
    return True, "User registered. You are now logged in."


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user = None


if not st.session_state.authenticated:
    st.markdown(
        """
        <style>
        .login-shell { max-width: 620px; margin: 48px auto; padding: 28px; background: #F5F4EC; border: 1px solid #C9C6B6; border-radius: 8px; }
        .login-title { font-family: 'Space Grotesk', sans-serif; font-size: 28px; color: #0C2124; margin-bottom: 8px; }
        .login-subtitle { color: #4B5A5A; margin-bottom: 18px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="login-shell">
            <div class="login-title">Water ATM Dashboard Access</div>
            <div class="login-subtitle">Sign in to view the atlas and reports.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mode = st.radio("Action", ["Log in", "Create account"], index=0, horizontal=True)

    if mode == "Log in":
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")

        if submitted:
            users = load_users()
            # check account lock for registered users
            if username in users:
                locked, secs = _is_locked(users, username)
                if locked:
                    mins = max(1, secs // 60)
                    st.error(f"Account locked due to repeated failures. Try again in {mins} minute(s).")
                else:
                    if authenticate(username, password):
                        _reset_failed_attempts(users, username)
                        st.session_state.authenticated = True
                        st.session_state.user = username
                        st.success("Logged in successfully.")
                        st.experimental_rerun()
                    else:
                        _record_failed_attempt(users, username)
                        entry = users.get(username, {})
                        remaining = max(0, 5 - int(entry.get("failed_attempts", 0)))
                        st.error(f"Invalid username or password. {remaining} attempt(s) remaining before lockout.")
            else:
                # Not a registered user: allow env-admin fallback only (do not create user records)
                if authenticate(username, password):
                    st.session_state.authenticated = True
                    st.session_state.user = username
                    st.success("Logged in successfully.")
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password.")

    else:
        with st.form("register_form"):
            r_user = st.text_input("Choose a username")
            r_pass = st.text_input("Choose a password", type="password")
            r_pass2 = st.text_input("Confirm password", type="password")
            reg = st.form_submit_button("Create account")

        if reg:
            if r_pass != r_pass2:
                st.error("Passwords do not match.")
            else:
                ok, msg = _validate_password_strength(r_pass)
                if not ok:
                    st.error(msg)
                else:
                    ok2, msg2 = register_user(r_user, r_pass)
                    if ok2:
                        st.session_state.authenticated = True
                        st.session_state.user = r_user
                        st.success(msg2)
                        st.experimental_rerun()
                    else:
                        st.error(msg2)

    st.stop()

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

/* ---- top masthead (refreshed) ---- */
.masthead {{
    background: linear-gradient(135deg, {INK}, {TEAL});
    color: #EAF3F1; padding: 34px 36px; border-radius: 12px; margin-bottom: 22px;
    position: relative; overflow: hidden; box-shadow: 0 8px 30px rgba(12,33,36,0.12);
}}
.masthead__row {{ display:grid; grid-template-columns: 1fr auto; gap: 18px; align-items:center; }}
.masthead .eyebrow {{
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; letter-spacing: .12em;
    color: {TEAL_BRIGHT}; text-transform: uppercase; margin-bottom: 6px;
}}
.masthead h1 {{
    font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 42px;
    margin: 0 0 6px; line-height: 1.05; color: #fff; letter-spacing: -0.02em;
}}
.masthead p {{ color: rgba(234,243,241,0.9); max-width: 720px; font-size: 15px; margin:0 0 14px; }}
.masthead__badge {{
    font-family: 'IBM Plex Mono', monospace; font-size: 11px; color: #EAF3F1;
    border: 1px solid rgba(234,243,241,0.08); border-radius: 999px; padding: 8px 14px;
    background: rgba(255,255,255,0.04);
}}
.masthead__badge b {{ color: {TEAL_BRIGHT}; display:block; font-size:14px; font-family:'Space Grotesk',sans-serif; }}

/* decorative floating droplet */
.masthead::after {{
    content: ""; position: absolute; right: -60px; top: -40px; width: 220px; height: 220px;
    background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.06), rgba(255,255,255,0.02) 30%, transparent 60%);
    transform: rotate(20deg); opacity: 0.9; pointer-events: none; filter: blur(8px);
}}

@media (max-width: 880px) {{
    .masthead__row {{ grid-template-columns: 1fr; gap: 10px; }}
    .masthead h1 {{ font-size: 30px; }}
}}

/* ---- tab bar styled as a real site nav ---- */
.stTabs [data-baseweb="tab-list"] {{
    background: {INK}; gap: 2px; padding: 0 38px; border-radius: 8px;
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

.site-footer {{
    margin-top: 32px; padding: 16px 4px 4px; border-top: 1px solid {LINE};
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;
}}
.site-footer__credit {{
    font-family: 'IBM Plex Mono', monospace; font-size: 11.5px; color: {SLATE};
}}
.site-footer__links a {{
    font-family: 'IBM Plex Mono', monospace; font-size: 11.5px; color: {TEAL};
    text-decoration: none; margin-left: 16px;
}}
.site-footer__links a:hover {{ text-decoration: underline; }}
</style>
""", unsafe_allow_html=True)

GITHUB_URL = "https://github.com/koushikgarg11"
LINKEDIN_URL = "https://www.linkedin.com/in/koushik-garg-b034442a9/"

def render_footer():
    st.markdown(f"""
    <div class="site-footer">
      <span class="site-footer__credit">Prepared by <b>Koushik</b> · Water ATM Downtime Atlas</span>
      <span class="site-footer__links">
        <a href="{GITHUB_URL}" target="_blank" rel="noopener">GitHub ↗</a>
        <a href="{LINKEDIN_URL}" target="_blank" rel="noopener">LinkedIn ↗</a>
      </span>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------- DATA LOAD ---
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "water_points.parquet"


@st.cache_data
def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Missing data file at {DATA_PATH}. Run build_data.py to generate it first."
        )
    return pd.read_parquet(DATA_PATH)


df = load_data()


# ------------------------------------------------------------- SIDEBAR -----
st.sidebar.markdown("### 💧 Water ATM Atlas")
if st.session_state.get("authenticated"):
    st.sidebar.success(f"Welcome, {st.session_state.get('user')}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.experimental_rerun()
st.sidebar.markdown("<span style='font-family:IBM Plex Mono,monospace;font-size:11px;color:#9FB6B2;'>FILTERS APPLY ACROSS ALL TABS</span>", unsafe_allow_html=True)
st.sidebar.markdown("---")

states = st.sidebar.multiselect("State / UT", sorted(df["State_Name"].unique()), default=[], key='states_sel')
sources = st.sidebar.multiselect("Water source tag", sorted(df["Water_Source"].unique()), default=[], key='sources_sel')
owners = st.sidebar.multiselect("Ownership type", sorted(df["Ownership_Type"].unique()), default=[], key='owners_sel')
flagged_only = st.sidebar.checkbox("Flagged points only", value=False, key='flagged_only')

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<span style='font-family:IBM Plex Mono,monospace;font-size:10.5px;color:#9FB6B2;line-height:1.5;'>"
    "No agency in India publishes a national Water ATM registry. This is OSM-tagged "
    "drinking-water infrastructure cross-checked against news coverage — a research "
    "signal, not an official census. See the Methodology tab."
    "</span>", unsafe_allow_html=True,
)

if "quick_flagged" not in st.session_state:
    st.session_state.quick_flagged = False

filtered = df.copy()
if states:
    filtered = filtered[filtered["State_Name"].isin(states)]
if sources:
    filtered = filtered[filtered["Water_Source"].isin(sources)]
if owners:
    filtered = filtered[filtered["Ownership_Type"].isin(owners)]
effective_flagged = bool(flagged_only) or bool(st.session_state.get("quick_flagged", False))
if effective_flagged:
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
        # Quick filter toolbar
        q1, q2, q3 = st.columns([1, 1, 1])
        with q1:
                if st.button("Toggle flagged only (quick)"):
                        st.session_state.quick_flagged = not st.session_state.quick_flagged
                        st.experimental_rerun()
        with q2:
                if st.button("Clear filters"):
                        st.session_state.states_sel = []
                        st.session_state.sources_sel = []
                        st.session_state.owners_sel = []
                        st.session_state.flagged_only = False
                        st.session_state.quick_flagged = False
                        st.experimental_rerun()
        with q3:
                st.write("")

        # Animated KPI cards (embedded HTML for smooth count-up)
        kpi_data = {
                "total": total,
                "states": n_states,
                "districts": n_districts,
                "flagged": n_flagged,
                "completeness": round(completeness, 1),
        }
        kpi_html = """
        <style>
        .kpi-row { display:flex; gap:14px; margin-bottom:12px; }
        .kpi-card { background:__PAPER2__; border:1px solid __LINE__; border-radius:8px; padding:14px 16px; flex:1; text-align:left; }
        .kpi-label { font-family: 'IBM Plex Mono', monospace; font-size:11px; color:__SLATE__; margin-top:6px; text-transform:uppercase; }
        .kpi-value { font-family: 'Space Grotesk', sans-serif; font-size:28px; font-weight:700; color:__INK__; }
        .kpi-value.flag { color: __AMBER__; }
        </style>
        <div class="kpi-row">
            <div class="kpi-card"><div class="kpi-value" data-target="__TOTAL__">0</div><div class="kpi-label">mapped points shown</div></div>
            <div class="kpi-card"><div class="kpi-value" data-target="__STATES__">0</div><div class="kpi-label">states / UTs</div></div>
            <div class="kpi-card"><div class="kpi-value" data-target="__DISTRICTS__">0</div><div class="kpi-label">districts</div></div>
            <div class="kpi-card"><div class="kpi-value flag" data-target="__FLAGGED__">0</div><div class="kpi-label">flagged signals</div></div>
            <div class="kpi-card"><div class="kpi-value" data-target="__COMPLETENESS__">0</div><div class="kpi-label">avg. field completeness</div></div>
        </div>
        <script>
        function animate(el, target, isPct){
            var start = 0; var dur = 900; var startTime = performance.now();
            function step(now){
                var t = Math.min(1, (now - startTime) / dur);
                var value = Math.floor(t * target);
                el.innerText = isPct ? ( (value/10).toFixed(1) + '%' ) : value.toLocaleString();
                if(t < 1) requestAnimationFrame(step);
                else if(isPct) el.innerText = target.toFixed(1) + '%';
            }
            requestAnimationFrame(step);
        }
        document.querySelectorAll('.kpi-value').forEach(function(el){
            var target = parseFloat(el.getAttribute('data-target'));
            var isPct = el.parentElement.nextElementSibling && el.parentElement.nextElementSibling.innerText.indexOf('completeness') !== -1;
            animate(el, isPct ? target*10 : target, isPct);
        });
        </script>
        """
        kpi_html = kpi_html.replace('__TOTAL__', str(kpi_data['total']))
        kpi_html = kpi_html.replace('__STATES__', str(kpi_data['states']))
        kpi_html = kpi_html.replace('__DISTRICTS__', str(kpi_data['districts']))
        kpi_html = kpi_html.replace('__FLAGGED__', str(kpi_data['flagged']))
        kpi_html = kpi_html.replace('__COMPLETENESS__', str(kpi_data['completeness']))
        kpi_html = kpi_html.replace('__PAPER2__', PAPER2)
        kpi_html = kpi_html.replace('__LINE__', LINE)
        kpi_html = kpi_html.replace('__SLATE__', SLATE)
        kpi_html = kpi_html.replace('__INK__', INK)
        kpi_html = kpi_html.replace('__AMBER__', AMBER)
        components.html(kpi_html, height=140)

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

        render_footer()


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
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet-search/2.9.9/leaflet-search.min.css">
                        <style>
                            html, body {{ margin:0; padding:0; }}
                            #map {{ height: 560px; width: 100%; border-radius: 8px; box-shadow: 0 6px 18px rgba(12,33,36,0.08); }}
                            .wa-pin {{ border-radius: 50% 50% 50% 0; transform: rotate(-45deg); display:block; box-shadow: 0 1px 2px rgba(0,0,0,0.12); }}
                            .wa-pin--teal {{ background: #2F9C8F; border: 2px solid #0C2124; }}
                            .wa-pin--amber {{ background: #E08F3C; border: 2px solid #0C2124; }}
                            .leaflet-popup-content {{ font-family: Inter, sans-serif; font-size: 13px; }}
                            .leaflet-control-search {{ box-shadow: 0 6px 14px rgba(12,33,36,0.12); border-radius: 6px; }}
                        </style>
                        <div id="map"></div>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.min.js"></script>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet-search/2.9.9/leaflet-search.min.js"></script>
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

                            const markersLayer = L.layerGroup();

                            function icon(flag) {{
                                return L.divIcon({{
                                    className: '',
                                    html: `<span class="wa-pin ${{flag ? 'wa-pin--amber' : 'wa-pin--teal'}}" style="width:14px;height:14px;"></span>`,
                                    iconSize: [14, 14], iconAnchor: [7, 14],
                                }});
                            }}

                            points.forEach(p => {{
                                const title = (p.v ? p.v + ', ' : '') + (p.d || '') + ' | ' + p.st;
                                const m = L.marker([p.lat, p.lon], {{ icon: icon(p.f), flagged: p.f, title: title }});
                                m.bindPopup(
                                    '<div style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#4B5A5A;text-transform:uppercase;">' +
                                        (p.f ? '⚠ Flagged by news signal' : 'No failure signal found') +
                                    '</div>' +
                                    '<div style="font-weight:600;margin:4px 0 2px;">' + (p.v ? p.v + ', ' : '') + (p.d || 'Unknown district') + '</div>' +
                                    '<div style="color:#4B5A5A;margin-bottom:6px;">' + p.st + '</div>' +
                                    '<div style="font-size:12px;color:#4B5A5A;">Source: ' + p.src + ' · Owner: ' + p.own + '</div>' +
                                    (p.url ? ('<a href="' + p.url + '" target="_blank" rel="noopener" style="font-size:12px;color:#155E5A;">View source →</a>') : '')
                                );
                                cluster.addLayer(m);
                                markersLayer.addLayer(m);
                            }});

                            map.addLayer(cluster);

                            // Add search control that looks up markers by their title (village, district, state)
                            var searchControl = new L.Control.Search({{
                                layer: markersLayer,
                                propertyName: 'title',
                                marker: false,
                                initial: false,
                                zoom: 12,
                                textPlaceholder: 'Search place or district...'
                            }});
                            searchControl.on('search:locationfound', function(e) {{
                                if(e.layer._popup) e.layer.openPopup();
                            }});
                            map.addControl(searchControl);

                            if (points.length > 0) {{
                                try {{ map.fitBounds(cluster.getBounds().pad(0.1)); }} catch (e) {{}}
                            }}
                        </script>
            """

        map_html = build_leaflet_map(tuple(states), tuple(sources), tuple(owners), effective_flagged)
        st.iframe(map_html, height=575)

        legend_col1, legend_col2 = st.columns([1, 4])
        legend_col1.markdown(
            f"<span style='color:{TEAL_BRIGHT};'>●</span> No signal &nbsp;&nbsp; "
            f"<span style='color:{AMBER_BRIGHT};'>●</span> Flagged",
            unsafe_allow_html=True,
        )

    render_footer()


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

    render_footer()


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

    render_footer()


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

    render_footer()
