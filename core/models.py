"""
models.py

Domain models used throughout the application.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Track:
    """
    Represents one audio file throughout the whole pipeline.
    """

    # File on disk
    path: Path

    # -------- Original metadata extracted from filename --------

    original_artist: str = ""
    original_title: str = ""

    # -------- Clean values used for searching --------

    search_artist: str = ""
    search_title: str = ""

    # -------- Information retrieved online --------

    album: str = ""
    artwork_url: str = ""
    artwork_path: Path | None = None
    provider: str = ""
    match_score: float = 0.0

    # -------- Processing state --------

    has_embedded_artwork: bool = False
    processed: bool = False
    error: str = ""

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def extension(self) -> str:
        return self.path.suffix.lower()

    @property
    def stem(self) -> str:
        return self.path.stem