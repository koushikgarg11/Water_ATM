"""
Rebuilds data/water_points.parquet from the master Excel file.

Usage (Git Bash, inside water_atm_streamlit/):
    python build_data.py path/to/water_atm_master_corrected.xlsx
"""
import sys
from pathlib import Path

import pandas as pd


def split_urls(u):
    if not isinstance(u, str):
        return "", ""
    parts = [p.strip() for p in u.split("|")]
    osm = next((p for p in parts if "openstreetmap" in p), "")
    news = next((p for p in parts if "openstreetmap" not in p), "")
    return osm, news


def main(xlsx_path):
    df = pd.read_excel(xlsx_path, engine="openpyxl")
    df[["osm_url", "news_url"]] = df["Source_URL"].apply(lambda u: pd.Series(split_urls(u)))
    df["Flagged"] = df["Current_Operational_Status"] != "Unknown"
    df["District_Name"] = df["District_Name"].replace("Unknown", pd.NA)
    df["Village_City_Name"] = df["Village_City_Name"].replace("Unknown", pd.NA)

    keep = ["Water_ATM_ID", "State_Name", "District_Name", "Village_City_Name",
            "Latitude", "Longitude", "Water_Source", "Ownership_Type",
            "Current_Operational_Status", "Flagged", "osm_url", "news_url",
            "data_completeness_pct"]
    out = df[keep].copy()

    out_dir = Path(__file__).resolve().parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "water_points.parquet"
    out.to_parquet(out_path, index=False)
    print(f"Rebuilt {out_path}: {len(out)} rows, {out['Flagged'].sum()} flagged.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build_data.py <path_to_xlsx>")
        sys.exit(1)
    main(sys.argv[1])
