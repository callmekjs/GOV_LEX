"""Raw API response archival utilities (data_index/raw)."""

from __future__ import annotations

import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


RAW_BASE_DIR = Path("data_index/raw")


def _slug(text: str, limit: int = 80) -> str:
    safe = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", text).strip("_")
    if not safe:
        safe = "raw"
    return safe[:limit]


def save_raw_response(payload: Any, source: str, key: str) -> Path:
    """원본 응답을 gzip JSON으로 보관한다.

    경로:
      data_index/raw/<source>/<YYYY-MM-DD>/<HHMMSS>_<key>.json.gz
    """
    day = datetime.now().strftime("%Y-%m-%d")
    ts = datetime.now().strftime("%H%M%S")
    source_dir = RAW_BASE_DIR / _slug(source) / day
    source_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"{ts}_{_slug(key)}.json.gz"
    out_path = source_dir / file_name

    with gzip.open(out_path, "wt", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return out_path
