"""Empirical hourly weather via Open-Meteo archive API (open, no key).

Persists raw JSON responses under data/raw/openmeteo/ and appends an
acquisition ledger row (URL, params, UTC time, sha256, bytes) to
data/raw/ACQUISITION_LEDGER.csv.
"""
import hashlib, json, os, csv, datetime
import numpy as np
import requests

RAW = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
LEDGER = os.path.join(RAW, "ACQUISITION_LEDGER.csv")
URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_hourly(lat, lon, start="2023-01-01", end="2023-12-31",
                 hourly=("temperature_2m",), tz="GMT"):
    os.makedirs(os.path.join(RAW, "openmeteo"), exist_ok=True)
    params = dict(latitude=lat, longitude=lon, start_date=start,
                  end_date=end, hourly=",".join(hourly), timezone=tz)
    r = requests.get(URL, params=params, timeout=120)
    r.raise_for_status()
    body = r.content
    sha = hashlib.sha256(body).hexdigest()
    tag = f"lat{lat:+.2f}_lon{lon:+.2f}_{start}_{end}"
    path = os.path.join(RAW, "openmeteo", f"{tag}.json")
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(body)
    _ledger(url=r.url, params=params, path=path, sha=sha, nbytes=len(body),
            license="CC-BY 4.0 Open-Meteo (ECMWF ERA5-based reanalysis)")
    data = json.loads(body)
    temps = np.array(data["hourly"]["temperature_2m"], dtype=float)
    return temps.reshape(-1, 24)[:365]


def _ledger(**row):
    exists = os.path.exists(LEDGER)
    row.setdefault("fetched_utc", datetime.datetime.utcnow().isoformat() + "Z")
    with open(LEDGER, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            w.writeheader()
        w.writerow(row)
