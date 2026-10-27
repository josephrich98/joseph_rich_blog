#!/usr/bin/env python3
"""Refresh the BioCartoon site-visit counts shown on the Jekyll software page.

The output contains aggregated counts only. API credentials are read from the
environment and are never written to the site.
"""

import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site/_data/biocartoon_metrics.json"
GRAPHQL = """query Visits($zone: string, $filter: filter) {
  viewer {
    zones(filter: {zoneTag: $zone}) {
      httpRequestsAdaptiveGroups(limit: 1, filter: $filter) {
        sum { visits }
      }
    }
  }
}"""


def get_json(url, token=None, data=None):
    headers = {"Accept": "application/json", "User-Agent": "joseph-rich-blog-metrics"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    with urlopen(Request(url, headers=headers, data=data), timeout=30) as response:
        return json.load(response)


def cloudflare_visits(hostname, token, zone, start, end):
    if not token or not zone:
        return None
    result = get_json(
        "https://api.cloudflare.com/client/v4/graphql",
        token,
        {
            "query": GRAPHQL,
            "variables": {
                "zone": zone,
                "filter": {
                    "datetime_geq": start,
                    "datetime_lt": end,
                    "clientRequestHTTPHost": hostname,
                    "requestSource": "eyeball",
                },
            },
        },
    )
    if result.get("errors"):
        raise RuntimeError(f"Cloudflare analytics query failed: {result['errors']}")
    zones = result["data"]["viewer"]["zones"]
    if len(zones) != 1:
        raise RuntimeError("Cloudflare analytics zone was not found")
    rows = zones[0]["httpRequestsAdaptiveGroups"]
    return sum(row["sum"]["visits"] for row in rows)


def main():
    now = dt.datetime.now(dt.timezone.utc)
    # Fourteen UTC calendar days, including today.
    start = (now.date() - dt.timedelta(days=13)).isoformat() + "T00:00:00Z"
    end = now.isoformat(timespec="seconds").replace("+00:00", "Z")
    cloudflare_token = os.getenv("CLOUDFLARE_ANALYTICS_TOKEN")
    cloudflare_zone = os.getenv("CLOUDFLARE_ZONE_ID")
    metrics = {
        "updated_at": end,
        "www_visits_14d": cloudflare_visits(
            "www.biocartoon.com", cloudflare_token, cloudflare_zone, start, end
        ),
        "app_visits_14d": cloudflare_visits(
            "app.biocartoon.com", cloudflare_token, cloudflare_zone, start, end
        ),
    }
    OUTPUT.write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"Updated {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
