"""
models.py

Domain models used by the artwork search pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ArtworkCandidate:
    """
    One artwork result returned by a provider, not yet scored.

    Exactly one of `url` / `local_path` is set: remote providers (iTunes,
    MusicBrainz) return a URL to download; the placeholder provider
    generates the image locally and returns its path directly.
    """

    provider: str

    artist: str
    title: str
    album: str = ""

    score: float = 0.0

    url: str = ""
    local_path: Path | None = None
