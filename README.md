<div align="center">

# 💧 Water ATM Downtime Atlas

**Mapping India's drinking-water infrastructure — and flagging where it's gone dark**

[**🔗 View Live Dashboard**](https://wateratm.streamlit.app) · [Report an Issue](#) · [Author](https://github.com/koushikgarg11)

</div>

---

## The problem

India has no official, centralized registry of public drinking-water points. Availability data is scattered across OpenStreetMap tags, sparse news coverage, and word of mouth — which means outages often go unnoticed until a community is already without water.

**Water ATM Downtime Atlas** pulls together ~36,856 OSM-tagged water infrastructure points across India, cross-references them against news mentions for signals of downtime, and puts the whole thing on an interactive, filterable map — built to surface a research signal, not to replace ground-truth verification.

## Why this build

This dashboard merges two earlier prototypes instead of picking one:

| From | What it contributes |
|---|---|
| **Streamlit app** | Sidebar filters, KPI row, and a one-click deploy-to-public-URL workflow — all kept in sync via Streamlit's rerun model |
| **Static HTML dashboard** | The actual map. Streamlit's built-in `pydeck` widget draws 36,856 overlapping dots at country zoom and becomes unreadable — so this version embeds the original Leaflet + marker-clustering map (same droplet pins, same popups) via `streamlit.components.v1.html`, fully driven by the sidebar filters |

**Net effect:** one app, filter-synced, publicly deployable, with a map that's actually usable at national scale.

---

## Features

- 🗺️ **Leaflet map with marker clustering** — amber pins for flagged (possible downtime) points, teal for no signal, full popup detail on hover
- 🎛️ **Synced sidebar filters** — state, water-source tag, ownership type, and a flagged-only toggle drive every chart, the map, the KPI row, and the data table simultaneously
- 📊 **Chart suite** — top districts by point density, water-source mix, ownership mix, top states
- 📋 **Flagged report table** — sortable, with a clickable Source column linking to the matched news article (or the raw OSM node when no article exists)
- 📤 **CSV export** for any filtered view

---

## Tech stack

`Python` · `Streamlit` · `Leaflet.js` · `Pandas` · `Parquet` · `OpenStreetMap Overpass API`

---

## Quickstart

### Run it locally (Git Bash)

```bash
cd water_atm_streamlit
python -m venv venv
source venv/Scripts/activate      # Git Bash on Windows
pip install -r requirements.txt
streamlit run app.py
```

Streamlit opens automatically at **http://localhost:8501**. If it doesn't, open that URL yourself. Stop it with `Ctrl+C`.

> On Mac/Linux, activate with `source venv/bin/activate` instead.

### Deploy it live (Streamlit Community Cloud — free)

Needs your code in a GitHub repo; Streamlit Cloud runs it from there.

```bash
# from Git Bash, inside water_atm_streamlit/
git init
git add .
git commit -m "Water ATM Downtime Atlas dashboard"
```

1. Create a new empty repo on GitHub — skip the README, you already have one.
2. Connect and push:
   ```bash
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git branch -M main
   git push -u origin main
   ```
3. Go to **[share.streamlit.io](https://share.streamlit.io)**, sign in with GitHub, click **New app**, pick your repo/branch, set the main file to `app.py`, and click **Deploy**.

You'll get a public URL like `https://<your-app-name>.streamlit.app`. Every future `git push` to `main` redeploys it automatically.

**Before you push publicly:** `data/water_points.parquet` is committed as-is and contains no personal data, so it's safe to make public. If the repo needs to stay private, Streamlit Community Cloud supports private repos on free accounts, with an invite-only app link.

### Other deploy targets

- **Hugging Face Spaces** — free, same workflow: push to a Space's git remote instead of GitHub, select "Streamlit" as the SDK
- **Render / Railway / a VPS** — start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

---

## Regenerating the data

Got an updated source Excel file? One command rebuilds the dataset in the exact shape `app.py` expects — no other code changes needed:

```bash
python build_data.py path/to/your_file.xlsx
```

---

## A performance tradeoff worth knowing about

Embedding a real Leaflet map inside Streamlit means the full point set (~6.5MB as JSON) ships to the browser on an unfiltered view. It's cached per filter combination, so revisiting a state you've already viewed is instant — but the *first* unfiltered load, and the first look at any new filter combination, will feel a beat slower than the old pydeck version. The app surfaces a small caption above the map whenever this applies.

If that tradeoff doesn't suit your use case, the pure-pydeck Streamlit version (earlier build) loads faster initially but isn't really usable at national zoom with this many points.

---

## Honest scope & limitations

> There is **no official Water ATM registry in India.** This dashboard cross-references OSM-tagged drinking-water infrastructure against news text to produce a *research signal* — not a verified operational status.

- Maharashtra and Kerala's high point counts reflect **OSM mapping density**, not superior service coverage.
- Flagged points need **manual verification** before any real decision leans on them.

---

<div align="center">

Built by [**Koushik Garg**](https://github.com/koushikgarg11) · Data Analyst Intern @ Analytics Career Connect

</div>
