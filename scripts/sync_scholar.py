"""Refresh the Google Scholar author bibliography using SerpApi."""

import json
import os
import re
import sys
import tempfile
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/scholar-cache.json"
AUTHOR = json.loads((ROOT / "data/profile.json").read_text())["scholarId"]


def fetch_page(start, key):
    params = {
        "engine": "google_scholar_author",
        "author_id": AUTHOR,
        "hl": "en",
        "sort": "pubdate",
        "num": 100,
        "start": start,
        "api_key": key,
    }
    try:
        with urlopen(
            "https://serpapi.com/search.json?" + urlencode(params), timeout=45
        ) as res:
            return json.load(res)
    except HTTPError as exc:
        raise ValueError(f"Scholar provider returned HTTP {exc.code}") from None
    except (URLError, TimeoutError, ValueError):
        raise ValueError("Scholar provider could not supply a JSON response") from None


def collect(fetch):
    records = {}
    start = 0
    while True:
        page = fetch(start)
        if page.get("error") or not isinstance(page.get("articles"), list):
            raise ValueError(
                "Scholar provider returned an error or omitted its articles"
            )
        rows = page["articles"]
        if not rows:
            raise ValueError("Scholar provider returned an empty page")
        for row in rows:
            citation = row.get("citation_id", "")
            title = row.get("title", "").strip()
            if (
                not re.fullmatch(re.escape(AUTHOR) + r":[A-Za-z0-9_-]+", citation)
                or not title
            ):
                raise ValueError("Scholar row lacks the expected author ID or title")
            year = str(row.get("year") or "")
            records[citation] = {
                "citation_id": citation,
                "title": title,
                "year": int(year) if re.fullmatch(r"\d{4}", year) else None,
                "authors": row.get("authors") or "",
                "venue": row.get("publication") or "Google Scholar record",
                "url": "https://scholar.google.com/citations?"
                + urlencode(
                    {
                        "view_op": "view_citation",
                        "user": AUTHOR,
                        "citation_for_view": citation,
                    }
                ),
            }
        next_url = (page.get("serpapi_pagination") or {}).get("next")
        if not next_url:
            break
        query = parse_qs(urlsplit(next_url).query)
        val = (query.get("start") or query.get("cstart") or [None])[0]
        if val is None or not val.isdigit() or int(val) <= start:
            raise ValueError("Invalid pagination offset")
        start = int(val)
    return list(records.values())


def sync():
    key = os.getenv("SERPAPI_KEY", "").strip()
    if not key:
        raise ValueError(
            "Set the SERPAPI_KEY repository secret to enable Scholar refreshes"
        )
    rows = collect(lambda start: fetch_page(start, key))
    updated = {
        "author_id": AUTHOR,
        "updated": date.today().isoformat(),
        "articles": rows,
    }
    # Replace only after the last page has been successfully validated.
    with tempfile.NamedTemporaryFile(
        "w", dir=CACHE.parent, delete=False, encoding="utf-8"
    ) as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)
        f.write("\n")
        temporary = Path(f.name)
    temporary.replace(CACHE)
    print(f"Collected {len(rows)} records for {AUTHOR}")


if __name__ == "__main__":
    try:
        sync()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        sys.exit(f"Publication refresh failed. Previous snapshot retained. {exc}")
