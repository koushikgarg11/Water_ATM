# Water ATM Downtime Atlas — Merged Edition

This merges the two previous versions instead of choosing between them:

- **From the Streamlit app**: the sidebar filters, KPI row, and deploy-to-a-
  public-URL workflow, all built on Streamlit's rerun model so everything
  stays in sync automatically.
- **From the static HTML dashboard**: the actual map. Streamlit's built-in
  map widget (pydeck) draws 36,856 raw overlapping dots at country zoom —
  unreadable. This version embeds the original Leaflet + marker-clustering
  map (same droplet pins, same popups) inside the Streamlit page via
  `streamlit.components.v1.html`, driven by whatever the sidebar has
  filtered.

Net effect: one app, filter-synced, deployable, with a map that's actually
readable at national scale.

## Run it locally with Git Bash

```bash
cd water_atm_streamlit
python -m venv venv
source venv/Scripts/activate      # Git Bash on Windows
pip install -r requirements.txt
streamlit run app.py
```

Streamlit opens automatically at **http://localhost:8501**. If it doesn't,
open that URL yourself. Stop it with `Ctrl+C` in Git Bash.

> On Mac/Linux the activate command is `source venv/bin/activate` instead.

## Deploying it live (Streamlit Community Cloud — free)

This is what people usually mean by "deploy a Streamlit app." It needs your
code in a GitHub repo; Streamlit Cloud runs it from there.

```bash
# from Git Bash, inside water_atm_streamlit/
git init
git add .
git commit -m "Water ATM Downtime Atlas dashboard"
```

1. Create a new empty repo on GitHub (github.com → New repository). Don't
   initialize it with a README — you already have one.
2. Connect and push:
   ```bash
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git branch -M main
   git push -u origin main
   ```
3. Go to **share.streamlit.io**, sign in with GitHub, click **New app**,
   pick your repo/branch, set the main file to `app.py`, and click **Deploy**.

That's it — you get a public URL like
`https://<your-app-name>.streamlit.app`. Any future `git push` to `main`
redeploys it automatically.

### Before you push publicly

The `data/water_points.parquet` file is committed as-is — it contains no
personal data, so this is safe to make public. If your repo needs to stay
private, Streamlit Community Cloud supports private repos on free accounts
tied to a GitHub account with an invite-only app link.

## Other deploy targets

- **Hugging Face Spaces**: also free, works the same way (push to a Space's
  git remote instead of GitHub, select "Streamlit" as the SDK).
- **Render / Railway / a VPS**: run `streamlit run app.py --server.port $PORT
  --server.address 0.0.0.0` as the start command.

## Regenerating the data

If you get an updated Excel file:

```bash
python build_data.py path/to/your_file.xlsx
```

This rewrites `data/water_points.parquet` in the exact shape `app.py`
expects — no other code changes needed.

## What's interactive

- **Sidebar filters**: state, water-source tag, ownership type, flagged-only
  toggle — every chart, the map, the KPI row, and the flagged table all react
  to the same filter state.
- **Map**: pydeck scatterplot, amber = flagged, teal = no signal, hover for
  detail.
- **Charts**: top districts, water-source mix, ownership mix, top states.
- **Flagged report table**: sortable, with a clickable "Source" column
  linking straight to the matched news article (or the OSM node if no
  article link exists).

## A performance tradeoff worth knowing about

Embedding a real Leaflet map inside Streamlit means the full point set
(~6.5MB as JSON) gets sent to your browser when no filters are applied.
It's cached per filter combination — so switching back to a state you've
already viewed is instant — but the very first *unfiltered* load, and the
first look at any new filter combination, will feel a beat slower than the
pydeck version did. The app shows a small caption above the map when this
applies. If that tradeoff doesn't work for your use case, the pure-pydeck
Streamlit version (previous zip) is faster on first load but the map
itself is not really usable at national zoom with this many points.

## Honest scope

Same caveat as the static version, worth repeating: there is no official
Water ATM registry in India. This is OSM-tagged drinking-water
infrastructure cross-referenced against news text — a research signal to
investigate, not a verified operational status. Maharashtra/Kerala's high
counts reflect OSM mapping density, not superior service coverage. Flagged
points need manual verification before any real decision leans on them.
