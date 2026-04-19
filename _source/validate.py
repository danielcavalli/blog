"""Lightweight build-time validation helpers."""

from __future__ import annotations

from pathlib import Path


def run_validation(base_path: str | Path, posts_dir: str | Path) -> bool:
    """Perform deterministic pre-build checks.

    The current checks are intentionally minimal to avoid slowing down builds:
    verify that the posts directory exists and is a directory.
    """
    _ = base_path  # Reserved for future checks.
    posts_path = Path(posts_dir)

    if not posts_path.exists():
        print(f"Validation error: posts directory not found: {posts_path}")
        return False

    if not posts_path.is_dir():
        print(f"Validation error: posts path is not a directory: {posts_path}")
        return False

    return True
