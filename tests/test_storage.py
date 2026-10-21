from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from src.utils.storage import write_bronze_json


def test_bronze_snapshots_are_immutable_and_content_addressed(tmp_path: Path) -> None:
    metadata = {"data_inicial": "2026-10-20", "data_final": "2026-10-20"}
    first_path, first_changed = write_bronze_json(
        tmp_path,
        source="focus",
        ingestion_date=date(2026, 10, 21),
        file_name="expectativas.json",
        records=[{"Indicador": "IPCA", "Mediana": 4.5}],
        request_metadata=metadata,
    )
    repeated_path, repeated_changed = write_bronze_json(
        tmp_path,
        source="focus",
        ingestion_date=date(2026, 10, 21),
        file_name="expectativas.json",
        records=[{"Indicador": "IPCA", "Mediana": 4.5}],
        request_metadata=metadata,
    )
    revised_path, revised_changed = write_bronze_json(
        tmp_path,
        source="focus",
        ingestion_date=date(2026, 10, 21),
        file_name="expectativas.json",
        records=[{"Indicador": "IPCA", "Mediana": 4.6}],
        request_metadata=metadata,
    )

    assert first_changed is True
    assert repeated_changed is False
    assert revised_changed is True
    assert first_path == repeated_path
    assert revised_path != first_path
    assert first_path.exists()
    assert revised_path.exists()

    document = json.loads(first_path.read_text(encoding="utf-8"))
    assert len(document["payload_sha256"]) == 64
    assert document["request"] == metadata
