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
