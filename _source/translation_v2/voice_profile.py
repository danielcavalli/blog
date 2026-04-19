"""Author voice profile loading and fingerprint helpers for translation_v2."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


VOICE_PROFILE_PATH = Path("WRITING_STYLE.md")


@dataclass(slots=True)
class AuthorVoiceProfile:
    """Author-facing voice profile loaded from repo policy text."""

    brief: str


def load_author_voice_profile(path: str | Path = VOICE_PROFILE_PATH) -> AuthorVoiceProfile:
    profile_path = Path(path)
    if not profile_path.exists():
        return AuthorVoiceProfile(brief="")
    return AuthorVoiceProfile(brief=profile_path.read_text(encoding="utf-8").strip())


def compute_author_voice_fingerprint(profile: AuthorVoiceProfile) -> str:
    digest = hashlib.sha256()
    digest.update(profile.brief.encode("utf-8"))
    return digest.hexdigest()

