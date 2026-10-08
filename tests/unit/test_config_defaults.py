"""Zero-config settings defaults are product behaviour.

``docker-compose.yml`` mounts ``.env`` as an *optional* ``env_file``, so on a clean
clone (no ``.env``, no exported variables) the app runs entirely on the fallbacks in
``app/config.py``. These tests pin that path — they build a fresh ``Settings`` with the
variable removed, so they never depend on the developer's local ``.env``.
"""

from __future__ import annotations

import re

import pytest

from app.config import BASE_DIR, Settings

THRESHOLD = "RAG_MIN_SCORE"


def _default_threshold(monkeypatch: pytest.MonkeyPatch) -> float:
    monkeypatch.delenv(THRESHOLD, raising=False)
    return Settings().rag_min_score


def test_rag_min_score_defaults_to_validated_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _default_threshold(monkeypatch) == 0.12


def test_rag_min_score_still_reads_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(THRESHOLD, "0.3")
    assert Settings().rag_min_score == 0.3


def test_shipped_env_templates_match_the_code_default(monkeypatch: pytest.MonkeyPatch) -> None:
    code_default = _default_threshold(monkeypatch)
    for name in (".env.example", ".env.local.example"):
        text = (BASE_DIR / name).read_text(encoding="utf-8")
        values = [float(raw) for raw in re.findall(rf"(?m)^{THRESHOLD}=(\S+)", text)]
        assert values, f"{name} does not pin {THRESHOLD}"
        assert values == [code_default], f"{name} drifted from the app/config.py default"
