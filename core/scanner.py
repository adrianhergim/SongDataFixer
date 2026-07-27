"""
scanner.py

Recursively scans a directory looking for supported audio files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from core.models import Track


class MusicScanner:
    """
    Recursively scans a music library.

    Example
    -------
        scanner = MusicScanner()

        for track in scanner.scan(Path("/music")):
            print(track.path)
    """

    SUPPORTED_EXTENSIONS = {
        ".mp3",
        ".flac",
        ".wav",
        ".aiff",
        ".aif",
    }

    def __init__(
        self,
        ignore_hidden: bool = True,
    ):
        self.ignore_hidden = ignore_hidden

    def scan(self, root: Path | str) -> Iterator[Track]:
        """
        Recursively scans a directory.

        Parameters
        ----------
        root
            Root music folder.

        Yields
        ------
        Track
        """

        root = Path(root)

        if not root.exists():
            raise FileNotFoundError(f"Folder does not exist: {root}")

        if not root.is_dir():
            raise NotADirectoryError(f"Not a directory: {root}")

        yield from self._scan_directory(root)

    def _scan_directory(self, directory: Path) -> Iterator[Track]:

        for item in sorted(directory.iterdir(), key=lambda p: p.name.lower()):

            if self.ignore_hidden and self._is_hidden(item):
                continue

            if item.is_dir():
                yield from self._scan_directory(item)
                continue

            if item.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            yield Track(path=item)

    @staticmethod
    def _is_hidden(path: Path) -> bool:
        """
        Returns True if the file or one of its parents is hidden.
        """

        return any(part.startswith(".") for part in path.parts)