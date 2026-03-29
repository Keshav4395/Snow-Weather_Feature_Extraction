#!/usr/bin/env python3
"""
convert_label_stations.py
Input: stations.txt (raw notepad file)
Output: stations_with_snow_label.csv (CSV with snow_possible Yes/No and snow_score 0-1)
Also writes overrides_template.csv for manual corrections.
"""

import re
import csv
from pathlib import Path
import math

INPUT = r"C:\Snow Project\ghcnd-stations.txt"   # change if needed
OUTPUT = "stations_with_snow_label.csv"
OVERRIDE_TEMPLATE = "overrides_template.csv"

def parse_line(line):
    # Remove leading/trailing whitespace and collapse multiple spaces
    s = line.strip()
    if not s:
        return None
    tokens = s.split()
    # Basic safety: need at least 5 tokens (id, lat, lon, elev, name)
    if len(tokens) < 5:
        return None
    station_id = tokens[0]
    try:
        lat = float(tokens[1])
        lon = float(tokens[2])
        elev = tokens[3]
        # elevation sometimes like '-26.0' or may be missing; handle gracefully
        try:
            elevation = float(elev)
        except ValueError:
            # if elevation token is non-numeric, try next token
            elevation = None
            # try to find first numeric token among next two
            for tok in tokens[3:6]:
                try:
                    elevation = float(tok)
                    break
                except:
                    continue
    except Exception as e:
        # fallback: not parseable
        return None

    # The remainder is station name (tokens[4:])
    name_raw = " ".join(tokens[4:]).strip()
    # Remove common trailing tags like 'GSN' and numeric site ids
    name = re.sub(r'\bGSN\b', '', name_raw, flags=re.IGNORECASE).strip()
    # strip trailing numeric code like '41196' or 4-6 digit numbers
    name = re.sub(r'\b\d{4,6}\b$', '', name).strip()
    # remove duplicate spaces
    name = re.sub(r'\s{2,}', ' ', name)

    return {
        "station_id": station_id,
        "latitude": lat,
        "longitude": lon,
        "elevation_m": elevation if elevation is not None else "",
        "name": name
    }

def snow_score_from_features(lat, elevation):
    """
    Returns a snow_score in [0,1] where higher means more likely snow.
    Heuristic: elevation weighted strongly, latitude moderately.
    """
    if elevation is None or elevation == "":
        elevation = 0.0
    # Normalise elevation: 0..4000 m -> 0..1 (cap at 4000)
    elev_norm = max(0.0, min(1.0, float(elevation) / 4000.0))
    lat_abs = abs(float(lat))
    # Normalise latitude: 0..90 -> 0..1 (focus on higher lat)
    lat_norm = max(0.0, min(1.0, lat_abs / 90.0))
    # Combine: give elevation higher weight (0.65 elev, 0.35 lat)
    score = 0.65 * elev_norm + 0.35 * lat_norm

    # Quick rules to force near-zero for obvious tropical low-elevation
    if lat_abs < 25 and float(elevation) < 300:
        score = score * 0.05  # strongly reduce
    # Force high score for extreme elevation
    if float(elevation) >= 3000:
        score = max(score, 0.95)
    # cap
    score = max(0.0, min(1.0, score))
    return score

def label_from_score(score, threshold=0.35):
    """
    Convert numeric score to Yes/No label.
    Default threshold 0.35 (tunable).
    """
    return "Yes" if score >= threshold else "No"

def main():
    in_path = Path(INPUT)
    if not in_path.exists():
        print(f"Input file not found: {INPUT}")
        return

    rows = []
    with in_path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            parsed = parse_line(raw)
            if parsed is None:
                continue
            score = snow_score_from_features(parsed["latitude"], parsed["elevation_m"])
            label = label_from_score(score, threshold=0.35)
            parsed["snow_score"] = round(score, 3)
            parsed["snow_possible"] = label
            rows.append(parsed)

    # Write CSV
    fieldnames = ["station_id","latitude","longitude","elevation_m","name","snow_score","snow_possible"]
    with open(OUTPUT, "w", newline='', encoding="utf-8") as csvf:
        writer = csv.DictWriter(csvf, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # Write an override template so you can manually correct labels
    with open(OVERRIDE_TEMPLATE, "w", newline='', encoding="utf-8") as ovf:
        writer = csv.writer(ovf)
        writer.writerow(["station_id","current_label","override_label (Yes/No)","notes"])
        # Write top ~100 or all depending on size: here we write all for simplicity
        for r in rows:
            writer.writerow([r["station_id"], r["snow_possible"], "",""])

    print(f"Wrote {len(rows)} stations to {OUTPUT}")
    print(f"Wrote override template to {OVERRIDE_TEMPLATE}")
    print("If you want a different threshold or weighting, edit 'threshold' or the scoring function in the script.")

if __name__ == "__main__":
    main()
