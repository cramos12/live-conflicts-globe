#!/usr/bin/env python3
"""Fetch the latest GDELT 2.0 event files and build points.json.

Runs in GitHub Actions every 30 minutes. Takes the newest GDELT export
plus the three before it (one hour of reporting), keeps conflict events
(CAMEO root codes 18 = assault, 19 = fight, 20 = mass violence) that
carry a location, groups them by place, and writes points.json next to
index.html so GitHub Pages serves it same-origin (no CORS problem).
"""
import csv
import io
import json
import sys
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone

BASE = "https://data.gdeltproject.org/gdeltv2"
KIND = {"18": "Assault", "19": "Fight / armed clash", "20": "Mass violence"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "live-conflicts-globe/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def latest_stem():
    text = get(f"{BASE}/lastupdate.txt").decode()
    first = text.strip().splitlines()[0]
    url = first.split()[-1]
    return url.rsplit("/", 1)[-1].replace(".export.CSV.zip", "")


def fetch_events(stem):
    raw = get(f"{BASE}/{stem}.export.CSV.zip")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        data = z.read(z.namelist()[0]).decode("utf-8", "replace")
    return list(csv.reader(io.StringIO(data), delimiter="\t"))


def main():
    stem = latest_stem()
    newest = datetime.strptime(stem, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    places = {}
    files_ok = 0
    for step in range(4):  # newest file + three before it = ~1 hour
        s = (newest - timedelta(minutes=15 * step)).strftime("%Y%m%d%H%M%S")
        try:
            rows = fetch_events(s)
        except Exception as e:  # a missing/late file is fine, others may work
            print(f"skip {s}: {e}")
            continue
        files_ok += 1
        for r in rows:
            if len(r) < 61 or r[28] not in KIND or not r[56] or not r[57]:
                continue
            try:
                lat, lon = float(r[56]), float(r[57])
                articles = int(r[33] or 0)
            except ValueError:
                continue
            key = r[52] or f"{lat:.2f},{lon:.2f}"
            p = places.setdefault(key, {
                "name": key, "country": r[53], "lat": lat, "lon": lon,
                "events": 0, "articles": 0, "kind": KIND[r[28]], "url": r[60],
                "_best": -1,
            })
            p["events"] += 1
            p["articles"] += articles
            if r[28] == "20" or (r[28] == "19" and p["kind"] == "Assault"):
                p["kind"] = KIND[r[28]]
            if articles > p["_best"]:
                p["_best"] = articles
                p["url"] = r[60]
    if files_ok == 0:
        print("No GDELT files fetched; leaving points.json untouched.")
        sys.exit(1)
    points = sorted(places.values(), key=lambda p: -p["articles"])[:400]
    for p in points:
        p.pop("_best", None)
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "GDELT 2.0 events (machine-coded from world news reports)",
        "window": "Conflict events reported in the last ~60 minutes of GDELT updates",
        "count": len(points),
        "points": points,
    }
    with open("points.json", "w") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"points.json written: {len(points)} places from {files_ok} file(s)")


if __name__ == "__main__":
    main()
