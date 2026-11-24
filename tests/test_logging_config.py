from __future__ import annotations

import json
import logging
from pathlib import Path

from src.utils.logging_config import configure_logging


def test_configure_logging_writes_structured_json(tmp_path: Path) -> None:
    log_path = configure_logging(tmp_path)

    logging.getLogger("test.pipeline").info("carga concluída")
    for handler in logging.getLogger().handlers:
        handler.flush()

    document = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
    assert document["level"] == "INFO"
    assert document["logger"] == "test.pipeline"
    assert document["message"] == "carga concluída"


def test_configure_logging_closes_previous_file_handlers(tmp_path: Path) -> None:
    configure_logging(tmp_path / "first")
    first_handlers = list(logging.getLogger().handlers)
    first_file_handlers = [h for h in first_handlers if isinstance(h, logging.FileHandler)]
    assert len(first_file_handlers) == 1

    configure_logging(tmp_path / "second")

    assert first_file_handlers[0].stream is None
