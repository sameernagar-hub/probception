"""Google Sheets CSV adapter for public Phase 1 rubric ingestion."""

from __future__ import annotations

import urllib.request


class GoogleSheetCsvAdapter:
    """Fetch public Google Sheet CSV exports behind the adapter boundary."""

    name = "google_sheet_csv"

    def fetch_csv(self, url: str, *, timeout: int = 30) -> str:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read().decode("utf-8-sig")
