"""Terminal presentation for builds and explicit translation updates."""

from __future__ import annotations

import shlex
import time
from collections.abc import Iterable
from dataclasses import dataclass

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text


_console = Console(highlight=False)
_verbose = False
_progress: TranslationProgress | None = None
_STAGE_LABELS = {
    "source_analysis": "Understanding the source",
    "terminology_policy": "Choosing terminology",
    "translate": "Writing the localization",
    "critique": "Reviewing the draft",
    "revise": "Refining the localization",
    "final_review": "Checking the final translation",
}
_COLORS = {"running": "cyan", "success": "green", "error": "red", "info": "cyan"}


def _elapsed(start: float, end: float | None = None) -> str:
    seconds = int((end if end is not None else time.monotonic()) - start)
    minutes, seconds = divmod(max(0, seconds), 60)
    return f"{minutes}:{seconds:02d}"


@dataclass
class _Stage:
    name: str
    started: float
    ended: float | None = None
    error: str | None = None


class TranslationProgress:
    """One bounded view of actual work; presentation never decides what to translate."""

    def __init__(self, total: int, candidate_dir: str | None, next_step: str | None) -> None:
        self.total = total
        self.candidate_dir = candidate_dir
        self.next_step = next_step
        self.current = 0
        self.updated = 0
        self.title = ""
        self.direction = ""
        self.stages: list[_Stage] = []
        self.completed: list[tuple[str, str]] = []
        self.started = time.monotonic()
        self.ended: float | None = None
        self.outcome = "running"
        self.error = ""
        self.spinner = Spinner("dots", style="cyan")
        self.live = Live(
            console=_console, get_renderable=self.render, refresh_per_second=4,
            transient=False, vertical_overflow="crop",
        ) if _console.is_terminal else None
        if self.live:
            self.live.start(refresh=True)
        else:
            log_block("Translating blog", [("Selected", f"{total} document{'s' if total != 1 else ''}")])

    def refresh(self) -> None:
        if self.live:
            self.live.refresh()

    def render(self) -> Panel:
        remaining = max(0, self.total - self.current - self.updated)
        counts = Text(f"{self.current} current", style="green")
        counts.append(f"  ·  {self.updated} updated", style="cyan")
        if self.outcome != "complete":
            counts.append(f"  ·  {remaining} remaining", style="dim")
        counts.append(f"  ·  {_elapsed(self.started, self.ended)}", style="dim")
        body: list = [counts]
        if self.title:
            body.extend([Text(), Text(self.title, style="bold"), Text(self.direction, style="dim")])
            table = Table.grid(padding=(0, 1), expand=True)
            table.add_column(width=1)
            table.add_column(ratio=1)
            table.add_column(justify="right", no_wrap=True)
            for stage in self.stages[-4:]:
                marker = Text("×", style="red") if stage.error else (
                    Text("✓", style="green") if stage.ended is not None else self.spinner
                )
                table.add_row(marker, Text(_STAGE_LABELS.get(stage.name, stage.name.replace("_", " "))),
                              Text(_elapsed(stage.started, stage.ended), style="dim"))
            body.extend([Text(), table])
        if self.completed:
            body.append(Text())
            for title, direction in self.completed[-3:]:
                body.append(Text.assemble(("✓ ", "green"), title, (f"  ·  {direction}", "dim")))
        if self.outcome == "complete":
            if not self.updated:
                body.extend([Text(), Text("All selected translations are already current.")])
            next_step = (
                "Review: dan blog diff --candidate-dir " + shlex.quote(self.candidate_dir)
                if self.candidate_dir else "Next: dan blog build"
            )
            body.extend([Text(), Text(self.next_step or next_step, style="cyan")])
        if self.error:
            body.extend([Text(), Text(self.error, style="red"), Text(
                "Accepted work is preserved. Rerun the command to resume completed stages.", style="dim",
            )])
        title = {
            "running": "Translating blog", "complete": "Candidates ready" if self.candidate_dir else "Translations ready",
            "failed": "Translation failed", "interrupted": "Translation interrupted",
        }[self.outcome]
        return Panel(Group(*body), title=Text(title, style="bold"), width=110,
                     border_style="red" if self.error else "cyan", box=box.ROUNDED)


def configure_console(*, verbose: bool) -> None:
    global _verbose
    _verbose = verbose


def start_translation_batch(total: int, *, candidate_dir: str | None = None,
                            next_step: str | None = None) -> None:
    global _progress
    shutdown_console()
    _progress = TranslationProgress(total, candidate_dir, next_step)


def record_translation_reuse() -> None:
    if _progress:
        _progress.current += 1
        _progress.refresh()


def start_artifact_status(artifact_key: str, title: str,
                          details: Iterable[tuple[str, object]] | None = None) -> None:
    direction = " · ".join(str(value) for _, value in (details or []))
    if _progress:
        _progress.title = title
        _progress.direction = direction
        _progress.stages = []
        _progress.refresh()
    if not _progress or not _progress.live:
        log_block(title, details)


def finish_artifact_status(result: str) -> None:
    if _progress:
        _progress.updated += 1
        _progress.completed.append((_progress.title, _progress.direction))
        _progress.title = ""
        _progress.stages = []
        _progress.refresh()


def finish_translation_batch(*, error: str | None = None, interrupted: bool = False) -> None:
    if not _progress:
        if error:
            log_line(error, status="error")
        return
    _progress.ended = time.monotonic()
    _progress.outcome = "interrupted" if interrupted else "failed" if error else "complete"
    _progress.error = error or ""
    if _progress.stages and _progress.stages[-1].ended is None:
        _progress.stages[-1].ended = _progress.ended
        _progress.stages[-1].error = error
    if not error:
        _progress.title = ""
    _progress.refresh()
    if not _progress.live:
        _console.print(_progress.render())


def shutdown_console() -> None:
    global _progress
    if _progress and _progress.live:
        _progress.live.stop()
    _progress = None


def start_stage_status(stage: str, artifact: str, action: str) -> None:
    if _progress:
        _progress.stages.append(_Stage(stage, time.monotonic()))
        _progress.refresh()
    if not _progress or not _progress.live:
        log_line(_STAGE_LABELS.get(stage, stage.replace("_", " ")), status="running")


def finish_stage_status(stage: str, artifact: str, *, result: str | None = None,
                        error: str | None = None,
                        extra_details: Iterable[tuple[str, object]] | None = None) -> None:
    if _progress and _progress.stages:
        current = _progress.stages[-1]
        current.ended = time.monotonic()
        current.error = error
        _progress.refresh()
    if error:
        log_line(error, status="error")
    elif _verbose and result:
        log_line(result, status="success")


def start_runner_status(*, stage: str, attempt: int, max_attempts: int,
                        model: str, attach_path: str) -> None:
    if _verbose:
        log_block("Model request", [("Stage", stage), ("Model", model),
                                   ("Attempt", f"{attempt}/{max_attempts}"), ("Source", attach_path)])
    elif attempt > 1:
        log_line(f"Retrying {_STAGE_LABELS.get(stage, stage).lower()} ({attempt}/{max_attempts})")


def finish_runner_status(*, stage: str, attempt: int, result: str | None = None,
                         error: str | None = None, action: str | None = None,
                         exit_code: int | None = None, classification: str | None = None) -> None:
    if error:
        log_line(error, status="error")
    elif _verbose and result:
        log_line(result, status="success")


def log_block(title: str, details: Iterable[tuple[str, object]] | None = None, *,
              indent: int = 0, style: str | None = None, status: str = "info") -> None:
    table = Table.grid(padding=(0, 2), expand=True)
    table.add_column(style="dim", no_wrap=True)
    table.add_column(ratio=1)
    for label, value in details or []:
        table.add_row(Text(str(label)), Text(str(value)))
    _console.print(Panel(table, title=Text(title, style="bold"), width=110,
                         border_style=_COLORS.get(status, "cyan")))


def log_line(message: str, *, indent: int = 0, status: str = "info") -> None:
    marker = {"running": "…", "success": "✓", "error": "×"}.get(status, "•")
    _console.print(Text.assemble((f"{marker} ", _COLORS.get(status, "cyan")), str(message)))


def log_blank() -> None:
    _console.print()


def log_build_footer(*, success: bool | None = None, outcome: str | None = None) -> None:
    resolved = outcome or ("success" if success else "failure")
    title = {"success": "Build complete", "interrupted": "Build interrupted", "failure": "Build failed"}[resolved]
    log_block(title, status="success" if resolved == "success" else "error")
