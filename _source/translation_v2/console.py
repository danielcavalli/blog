"""Rich console helpers for translation_v2 build logs."""

from __future__ import annotations

import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass, field

from rich import box
from rich.align import Align
from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


_console = Console(highlight=False, soft_wrap=True)
_current_session: _ArtifactSession | None = None
_dashboard: _TranslationDashboard | None = None
_verbose = False
_STAGE_ORDER = (
    "source_analysis",
    "terminology_policy",
    "translate",
    "critique",
    "revise",
    "final_review",
)
_TAPE_ROWS = 6
_ANIMATION_FPS = 6


@dataclass(slots=True)
class _LogBlock:
    key: str
    title: str
    details: list[tuple[str, str]] = field(default_factory=list)
    indent: int = 0
    style: str | None = None
    status: str = "info"


@dataclass(slots=True)
class _TapeEntry:
    message: str
    status: str = "info"


class _ArtifactSession:
    def __init__(
        self,
        *,
        artifact_key: str,
        title: str,
        details: Iterable[tuple[str, object]] | None,
    ) -> None:
        self.artifact_key = artifact_key
        self._blocks: list[_LogBlock] = [
            _LogBlock(
                key="artifact",
                title=title,
                details=_normalize_details(details),
                indent=1,
                status="running",
            )
        ]
        self._current_stage_keys: dict[str, str] = {}
        for stage in _STAGE_ORDER:
            stage_key = f"stage:{stage}"
            self._current_stage_keys[stage] = stage_key
            self._blocks.append(
                _LogBlock(
                    key=stage_key,
                    title=f"stage {stage}",
                    details=[("State", "pending")],
                    indent=2,
                    status="pending",
                )
            )
        self._current_runner_key: str | None = None

    def render(self) -> RenderableType:
        artifact = self._find_block("artifact")
        if artifact is None:
            return Text("")
        return Padding(_render_artifact_card(artifact, self._blocks[1:]), (0, 0, 0, 1))

    def upsert_artifact_details(self, details: Iterable[tuple[str, object]]) -> None:
        self._replace_block_details("artifact", details)

    def start_stage(self, stage: str, artifact: str, action: str) -> None:
        stage_key = self._current_stage_keys.get(stage)
        if stage_key is None:
            return
        self._current_runner_key = None
        self._replace_or_add_block(
            key=stage_key,
            title=f"stage {stage}",
            details=[
                ("State", "running"),
                ("Action", action),
            ],
            indent=2,
            status="running",
        )

    def finish_stage(
        self,
        stage: str,
        artifact: str,
        *,
        result: str | None = None,
        error: str | None = None,
        extra_details: Iterable[tuple[str, object]] | None = None,
    ) -> None:
        stage_key = self._current_stage_keys.get(stage)
        if stage_key is None:
            return

        details: list[tuple[str, object]] = [
            ("State", "done" if error is None else "error"),
        ]
        if result is not None:
            details.append(("Result", result))
        if error is not None:
            details.append(("Error", error))
        if extra_details is not None:
            details.extend(extra_details)
        self._replace_block_details(stage_key, details)
        block = self._find_block(stage_key)
        if block is not None:
            block.status = "error" if error is not None else "success"
        self._current_runner_key = None

    def start_runner(
        self,
        *,
        stage: str,
        attempt: int,
        max_attempts: int,
        model: str,
        attach_path: str,
    ) -> None:
        stage_key = self._current_stage_keys.get(stage)
        if stage_key is None:
            return

        runner_key = f"{stage_key}:runner"
        self._current_runner_key = runner_key
        details = [
            ("Stage", stage),
            ("Attempt", f"{attempt}/{max_attempts}"),
            ("Model", model),
            ("Attach", attach_path),
        ]
        block = self._find_block(runner_key)
        if block is None:
            self._blocks.append(
                _LogBlock(
                    key=runner_key,
                    title="runner",
                    details=_normalize_details(details),
                    indent=3,
                    style="dim",
                    status="running",
                )
            )
        else:
            block.details = _normalize_details(details)
            block.status = "running"

    def finish_runner(
        self,
        *,
        stage: str,
        attempt: int,
        result: str | None = None,
        error: str | None = None,
        action: str | None = None,
        exit_code: int | None = None,
        classification: str | None = None,
    ) -> None:
        stage_key = self._current_stage_keys.get(stage)
        if stage_key is None:
            return

        runner_key = self._current_runner_key or f"{stage_key}:runner"
        details: list[tuple[str, object]] = [
            ("Stage", stage),
            ("Attempt", attempt),
        ]
        if result is not None:
            details.append(("Result", result))
        if error is not None:
            details.append(("Error", error))
        if action is not None:
            details.append(("Action", action))
        if exit_code is not None:
            details.append(("Exit code", exit_code))
        if classification is not None:
            details.append(("Class", classification))
        self._replace_or_add_block(
            key=runner_key,
            title="runner",
            details=details,
            indent=3,
            style="dim",
            status="error" if error is not None else "success",
        )

    def _replace_block_details(
        self,
        key: str,
        details: Iterable[tuple[str, object]],
    ) -> None:
        block = self._find_block(key)
        if block is None:
            return
        block.details = _normalize_details(details)

    def _replace_or_add_block(
        self,
        *,
        key: str,
        title: str,
        details: Iterable[tuple[str, object]],
        indent: int,
        style: str | None = None,
        status: str = "info",
    ) -> None:
        block = self._find_block(key)
        if block is None:
            self._blocks.append(
                _LogBlock(
                    key=key,
                    title=title,
                    details=_normalize_details(details),
                    indent=indent,
                    style=style,
                    status=status,
                )
            )
            return
        block.title = title
        block.details = _normalize_details(details)
        block.indent = indent
        block.style = style
        block.status = status

    def _find_block(self, key: str) -> _LogBlock | None:
        for block in self._blocks:
            if block.key == key:
                return block
        return None


class _TranslationDashboard:
    def __init__(self, *, console: Console) -> None:
        self._console = console
        self._session: _ArtifactSession | None = None
        self._events: list[_TapeEntry] = []
        self._live = Live(
            console=console,
            auto_refresh=True,
            refresh_per_second=_ANIMATION_FPS,
            transient=False,
            vertical_overflow="visible",
            get_renderable=self.render,
        )
        self._live.start()

    def set_session(self, session: _ArtifactSession | None, *, refresh: bool = True) -> None:
        self._session = session
        if refresh:
            self.refresh()

    def append_event(self, *, message: str, status: str, refresh: bool = True) -> None:
        self._events.append(_TapeEntry(message=message, status=status))
        self._events = self._events[-10:]
        if refresh:
            self.refresh()

    def refresh(self) -> None:
        self._live.update(self.render(), refresh=True)

    def stop(self) -> None:
        self.refresh()
        self._live.stop()

    def render(self) -> RenderableType:
        parts: list[RenderableType] = []
        if self._session is not None:
            parts.append(self._session.render())
        if self._events:
            parts.append(Padding(_render_tape_panel(self._events), (0, 0, 0, 1)))
        if not parts:
            return Text("")
        return Group(*parts)


def configure_console(*, verbose: bool) -> None:
    """Configure runtime console verbosity."""

    global _verbose
    _verbose = bool(verbose)


def log_block(
    title: str,
    details: Iterable[tuple[str, object]] | None = None,
    *,
    indent: int = 0,
    style: str | None = None,
    status: str = "info",
) -> None:
    """Print a styled info block."""

    block = _block_from(title, details, indent, style, status)
    if indent <= 1:
        _console.print(Padding(_render_static_panel(block), (0, 0, 0, indent)))
        return
    _console.print(Padding(_render_compact_block(block), (0, 0, 0, indent * 2)))


def log_detail(label: str, value: object, *, indent: int = 0) -> None:
    """Print one compact key/value line."""

    table = Table.grid(expand=False)
    table.add_column(style="bold #7dd3fc")
    table.add_column(style="white")
    table.add_row(f"{label.strip()}:", "" if value is None else str(value).strip())
    _console.print(Padding(table, (0, 0, 0, indent * 2)))


def log_line(
    message: str,
    *,
    indent: int = 0,
    status: str = "info",
) -> None:
    """Print one compact status line inside the current visual language."""

    table = Table.grid(expand=True)
    table.add_column(width=8)
    table.add_column(ratio=1)
    table.add_row(_status_badge(status), Text(str(message), style="white"))
    _console.print(Padding(table, (0, 0, 0, indent * 2)))


def log_blank() -> None:
    _console.print()


def log_build_footer(
    *,
    success: bool | None = None,
    outcome: str | None = None,
) -> None:
    """Print a surf-themed closing panel at the end of a build run."""

    resolved = outcome
    if resolved is None:
        resolved = "success" if success else "failure"

    if resolved == "success":
        title = "build complete"
        message = "build complete"
        border_style = "#22c55e"
    elif resolved == "interrupted":
        title = "build interrupted"
        message = "build interrupted by user"
        border_style = "#f59e0b"
    else:
        title = "build failed"
        message = "build failed"
        border_style = "#ef4444"

    text = Text(justify="center")
    text.append(message, style=f"bold {border_style}")
    panel = Panel.fit(
        Align.center(text),
        box=box.ROUNDED,
        border_style=border_style,
        title=f"[bold]{title}[/bold]",
        padding=(0, 2),
    )
    _console.print()
    _console.print(panel)


def record_translation_event(message: str, *, status: str = "info") -> None:
    """Append one settled translation event to the live tape when available."""

    dashboard = _ensure_dashboard()
    if dashboard is not None:
        dashboard.append_event(message=message, status=status)
        return
    log_line(message, indent=1, status=status)


def start_artifact_status(
    artifact_key: str,
    title: str,
    details: Iterable[tuple[str, object]] | None = None,
) -> None:
    """Start a live-updating artifact card when stdout is interactive."""

    global _current_session
    stop_artifact_status()
    if not _supports_live_updates():
        log_block(title, details, indent=1, status="running")
        return
    dashboard = _ensure_dashboard()
    if dashboard is None:
        log_block(title, details, indent=1, status="running")
        return
    _current_session = _ArtifactSession(
        artifact_key=artifact_key,
        title=title,
        details=details,
    )
    dashboard.set_session(_current_session)


def update_artifact_status(details: Iterable[tuple[str, object]]) -> None:
    if _current_session is None:
        return
    _current_session.upsert_artifact_details(details)
    dashboard = _ensure_dashboard()
    if dashboard is not None:
        dashboard.refresh()


def finish_artifact_status(result: str) -> None:
    global _current_session
    if _current_session is None:
        return
    block = _current_session._find_block("artifact")
    details = block.details if block is not None else []
    filtered = [(label, value) for label, value in details if label != "Result"]
    filtered.append(("Result", result))
    _current_session.upsert_artifact_details(filtered)
    if block is not None:
        block.status = "success"
    message = _artifact_event_message(_current_session, result=result)
    dashboard = _ensure_dashboard()
    if dashboard is not None:
        dashboard.append_event(message=message, status="success", refresh=False)
        dashboard.set_session(None, refresh=True)
    _current_session = None


def fail_artifact_status(error: str) -> None:
    global _current_session
    if _current_session is None:
        return
    block = _current_session._find_block("artifact")
    details = block.details if block is not None else []
    filtered = [
        (label, value)
        for label, value in details
        if label not in {"Result", "Error"}
    ]
    filtered.append(("Error", error))
    _current_session.upsert_artifact_details(filtered)
    if block is not None:
        block.status = "error"
    message = _artifact_event_message(_current_session, error=error)
    dashboard = _ensure_dashboard()
    if dashboard is not None:
        dashboard.append_event(message=message, status="error", refresh=False)
        dashboard.set_session(None, refresh=True)
    _current_session = None


def stop_artifact_status() -> None:
    global _current_session
    _current_session = None
    if _dashboard is not None:
        _dashboard.set_session(None)


def shutdown_console() -> None:
    """Stop any active live session before emitting terminal-safe final output."""

    global _dashboard
    stop_artifact_status()
    if _dashboard is not None:
        _dashboard.stop()
        _dashboard = None


def start_stage_status(stage: str, artifact: str, action: str) -> None:
    if _current_session is None:
        log_block(
            f"stage {stage}",
            [("State", "moving"), ("Action", action)],
            indent=2,
            status="running",
        )
        return
    _current_session.start_stage(stage, artifact, action)
    dashboard = _ensure_dashboard()
    if dashboard is not None:
        dashboard.refresh()


def finish_stage_status(
    stage: str,
    artifact: str,
    *,
    result: str | None = None,
    error: str | None = None,
    extra_details: Iterable[tuple[str, object]] | None = None,
) -> None:
    if _current_session is None:
        details: list[tuple[str, object]] = [
            ("State", "arrived" if error is None else "rupture")
        ]
        if result is not None:
            details.append(("Result", result))
        if error is not None:
            details.append(("Error", error))
        if extra_details is not None:
            details.extend(extra_details)
        log_block(
            f"stage {stage}",
            details,
            indent=2,
            status="error" if error is not None else "success",
        )
        return
    _current_session.finish_stage(
        stage,
        artifact,
        result=result,
        error=error,
        extra_details=extra_details,
    )
    dashboard = _ensure_dashboard()
    if dashboard is not None:
        dashboard.refresh()


def start_runner_status(
    *,
    stage: str,
    attempt: int,
    max_attempts: int,
    model: str,
    attach_path: str,
) -> None:
    if _current_session is None:
        log_block(
            "runner",
            [
                ("Stage", stage),
                ("Attempt", f"{attempt}/{max_attempts}"),
                ("Model", model),
                ("Attach", attach_path),
            ],
            indent=3,
            style="dim",
            status="running",
        )
        return
    _current_session.start_runner(
        stage=stage,
        attempt=attempt,
        max_attempts=max_attempts,
        model=model,
        attach_path=attach_path,
    )
    dashboard = _ensure_dashboard()
    if dashboard is not None:
        dashboard.refresh()


def finish_runner_status(
    *,
    stage: str,
    attempt: int,
    result: str | None = None,
    error: str | None = None,
    action: str | None = None,
    exit_code: int | None = None,
    classification: str | None = None,
) -> None:
    if _current_session is None:
        details: list[tuple[str, object]] = [
            ("Stage", stage),
            ("Attempt", attempt),
        ]
        if result is not None:
            details.append(("Result", result))
        if error is not None:
            details.append(("Error", error))
        if action is not None:
            details.append(("Action", action))
        if exit_code is not None:
            details.append(("Exit code", exit_code))
        if classification is not None:
            details.append(("Class", classification))
        log_block(
            "runner",
            details,
            indent=3,
            style="dim",
            status="error" if error is not None else "success",
        )
        return
    _current_session.finish_runner(
        stage=stage,
        attempt=attempt,
        result=result,
        error=error,
        action=action,
        exit_code=exit_code,
        classification=classification,
    )
    dashboard = _ensure_dashboard()
    if dashboard is not None:
        dashboard.refresh()


def _supports_live_updates() -> bool:
    return bool(_console.is_terminal and sys.stdout.isatty())


def _ensure_dashboard() -> _TranslationDashboard | None:
    global _dashboard
    if not _supports_live_updates():
        return None
    if _dashboard is None:
        _dashboard = _TranslationDashboard(console=_console)
    return _dashboard


def _block_from(
    title: str,
    details: Iterable[tuple[str, object]] | None,
    indent: int,
    style: str | None,
    status: str,
) -> _LogBlock:
    return _LogBlock(
        key="static",
        title=title,
        details=_normalize_details(details),
        indent=indent,
        style=style,
        status=status,
    )


def _normalize_details(details: Iterable[tuple[str, object]] | None) -> list[tuple[str, str]]:
    if details is None:
        return []
    cleaned: list[tuple[str, str]] = []
    for label, value in details:
        rendered_label = str(label).strip()
        if not rendered_label:
            continue
        cleaned.append((rendered_label, "" if value is None else str(value).strip()))
    return cleaned


def _render_static_panel(block: _LogBlock) -> RenderableType:
    details = _render_details_table(block.details)
    panel = Panel(
        details,
        box=box.ROUNDED,
        border_style=_status_color(block.status),
        title=_title_text(block.title, block.status),
        padding=(0, 1),
    )
    return panel


def _render_compact_block(block: _LogBlock) -> RenderableType:
    table = Table.grid(expand=True)
    table.add_column(width=10)
    table.add_column(width=18, style="bold white")
    table.add_column(ratio=1)
    table.add_row(_status_badge(block.status), block.title, _detail_summary(block))
    return table


def _render_artifact_card(
    artifact: _LogBlock,
    blocks: list[_LogBlock],
) -> RenderableType:
    action = _detail_value(artifact.details, "Action")
    details = [(label, value) for label, value in artifact.details if label != "Action"]
    body: list[RenderableType] = []
    if action:
        body.append(_render_focus_line(action))
    if details:
        body.append(_render_details_table(details))
    stage_rows = _render_stage_table(blocks)
    if stage_rows is not None:
        body.append(Text(""))
        body.append(stage_rows)
    panel = Panel(
        Group(*body),
        box=box.ROUNDED,
        border_style=_status_color(artifact.status),
        title=_title_text(artifact.title, artifact.status),
        padding=(0, 1),
    )
    return panel


def _render_focus_line(action: str) -> RenderableType:
    text = Text()
    text.append("current action  ", style="bold #7dd3fc")
    text.append(action, style="bold white")
    return Padding(text, (0, 0, 0, 0))


def _render_details_table(details: list[tuple[str, str]]) -> RenderableType:
    table = Table.grid(expand=True)
    table.add_column(style="bold #7dd3fc", ratio=1)
    table.add_column(style="white", ratio=3)
    for label, value in details:
        table.add_row(f"{label}", value)
    return table


def _render_stage_table(blocks: list[_LogBlock]) -> RenderableType | None:
    visible = [
        block
        for block in blocks
        if _verbose or block.title != "runner"
    ]
    if not visible:
        return None

    table = Table(
        show_header=False,
        box=box.SIMPLE_HEAVY,
        border_style="#1e3a5f",
        pad_edge=False,
        expand=True,
    )
    table.add_column(width=12)
    table.add_column(width=18, style="bold")
    table.add_column(ratio=1)
    def _sort_key(block: _LogBlock) -> tuple[int, str]:
        if block.title.startswith("stage "):
            stage_name = block.title.replace("stage ", "")
            try:
                return (_STAGE_ORDER.index(stage_name), "")
            except ValueError:
                return (len(_STAGE_ORDER), stage_name)
        return (len(_STAGE_ORDER) + 1, block.title)

    for block in sorted(visible, key=_sort_key):
        label = block.title.replace("stage ", "").replace("_", " ")
        if block.title == "runner":
            label = "runner"
        detail = _detail_summary(block)
        style = "dim" if block.title == "runner" else "white"
        table.add_row(
            _status_badge(block.status),
            Text(label, style=style),
            Text(detail, style=style),
        )
    return table


def _render_tape_panel(events: list[_TapeEntry]) -> RenderableType:
    table = Table.grid(expand=True)
    table.add_column(width=8)
    table.add_column(ratio=1)
    for entry in events:
        table.add_row(_status_badge(entry.status), Text(entry.message, style="white"))
    remaining_rows = max(0, _TAPE_ROWS - len(events))
    for _ in range(remaining_rows):
        table.add_row(Text(""), Text(""))
    return Panel(
        table,
        box=box.ROUNDED,
        border_style="#1e3a5f",
        title=Text("settled translations", style="bold white"),
        padding=(0, 1),
    )


def _detail_summary(block: _LogBlock) -> str:
    details = list(block.details)
    if not details:
        return ""
    head = details[0][1]
    tail = [f"{label.lower()}={value}" for label, value in details[1:]]
    if not tail:
        return head
    return f"{head} | " + " | ".join(tail)


def _detail_value(details: list[tuple[str, str]], label: str) -> str | None:
    for current_label, value in details:
        if current_label == label:
            return value
    return None


def _artifact_event_message(
    session: _ArtifactSession,
    *,
    result: str | None = None,
    error: str | None = None,
) -> str:
    artifact_block = session._find_block("artifact")
    title = "translation"
    if artifact_block is not None:
        title = artifact_block.title.replace("translation_v2 ", "", 1)
    if error is not None:
        return f"{title} failed: {error}"
    if result == "cache_hit":
        return f"{title} cache hit"
    if result == "cache_miss":
        return f"{title} translated"
    if result == "revision":
        return f"{title} revised"
    return f"{title} complete"


def _title_text(title: str, status: str) -> Text:
    text = Text()
    if title.startswith("translation_v2 ") and status == "running":
        wave = _wave_frame()
        text.append(wave + " ", style="bold #38bdf8")
    else:
        marker = _status_badge(status)
        text.append(marker.plain + " ", style=marker.style)
    text.append(title, style="bold white")
    return text


def _status_badge(status: str) -> Text:
    if status == "running":
        return Text("[..]", style="bold #38bdf8")
    if status == "success":
        return Text("[ok]", style="bold #22c55e")
    if status == "error":
        return Text("[x]", style="bold #ef4444")
    if status == "pending":
        return Text("[ ]", style="bold #7dd3fc")
    return Text("[-]", style="bold #38bdf8")


def _status_color(status: str) -> str:
    if status == "running":
        return "#38bdf8"
    if status == "success":
        return "#22c55e"
    if status == "error":
        return "#ef4444"
    if status == "pending":
        return "#7dd3fc"
    return "#7dd3fc"


def _wave_frame() -> str:
    frames = [
        "𓆝 𓈒𓏸𓂃",
        "𓈒 𓆝 𓏸𓂃",
        "𓈒𓏸 𓆝 𓂃",
        "𓈒𓏸𓂃 𓆝",
        "ꕀ﹏ 𓈒𓏸",
        "☼𓏲 𓈒𓏸𓂃",
        "𓈒 ☼𓏲 𓏸𓂃",
        "𓈒𓏸 ☼𓏲 𓂃",
        "𓈒𓏸𓂃 ☼𓏲",
        "﹏ꕀ 𓂃𓂁𓂃",
    ]
    return frames[int(time.monotonic() * 8) % len(frames)]
