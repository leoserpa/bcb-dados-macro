"""Atomic and deterministic local lakehouse storage helpers."""

from __future__ import annotations

import json
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any


def write_bronze_json(
    bronze_root: Path,
    *,
    source: str,
    ingestion_date: date,
    file_name: str,
    records: list[dict[str, Any]],
    request_metadata: dict[str, Any] | None = None,
) -> tuple[Path, bool]:
    """Write an immutable content-addressed raw snapshot."""
    request_metadata = request_metadata or {}
    canonical_payload = json.dumps(
        {
            "source": source,
            "ingestion_date": ingestion_date.isoformat(),
            "request": request_metadata,
            "records": records,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    payload_sha256 = sha256(canonical_payload.encode("utf-8")).hexdigest()
    original_name = Path(file_name)
    immutable_name = f"{original_name.stem}__{payload_sha256[:16]}{original_name.suffix}"
    target = (
        bronze_root
        / f"source={source}"
        / f"ingestion_date={ingestion_date.isoformat()}"
        / immutable_name
    )
    document = {
        "source": source,
        "ingestion_date": ingestion_date.isoformat(),
        "payload_sha256": payload_sha256,
        "record_count": len(records),
        "request": request_metadata,
        "records": records,
    }
    content = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if target.exists():
        return target, False

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(f"{target.suffix}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(target)
    return target, True
