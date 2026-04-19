"""CLI entrypoint tests for build.py."""

from __future__ import annotations

import os
import sys


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
if _SOURCE not in sys.path:
    sys.path.insert(0, _SOURCE)

import build  # noqa: E402


def test_main_passes_verbose_flag_to_build(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_build(**kwargs):  # noqa: ANN003
        captured.update(kwargs)
        return True

    footer_calls: list[dict[str, object]] = []
    shutdown_calls: list[str] = []

    monkeypatch.setattr(build, "build", _fake_build)
    monkeypatch.setattr(build, "shutdown_console", lambda: shutdown_calls.append("shutdown"))
    monkeypatch.setattr(
        build,
        "log_build_footer",
        lambda **kwargs: footer_calls.append(kwargs),
    )

    exit_code = build.main(["--verbose"])

    assert exit_code == 0
    assert captured["verbose"] is True
    assert shutdown_calls == ["shutdown"]
    assert footer_calls == [{"success": True}]


def test_main_handles_keyboard_interrupt_gracefully(monkeypatch):
    footer_calls: list[dict[str, object]] = []
    shutdown_calls: list[str] = []

    def _interrupting_build(**kwargs):  # noqa: ANN003, ARG001
        raise KeyboardInterrupt

    monkeypatch.setattr(build, "build", _interrupting_build)
    monkeypatch.setattr(build, "shutdown_console", lambda: shutdown_calls.append("shutdown"))
    monkeypatch.setattr(
        build,
        "log_build_footer",
        lambda **kwargs: footer_calls.append(kwargs),
    )

    exit_code = build.main([])

    assert exit_code == 130
    assert shutdown_calls == ["shutdown"]
    assert footer_calls == [{"outcome": "interrupted"}]
