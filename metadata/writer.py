"""
writer.py

Renames audio files and writes metadata.
"""

from __future__ import annotations

from mutagen import File
from mutagen.flac import FLAC
from mutagen.id3 import TIT2, TPE1

from core.models import Track


class MetadataWriter:
    """
    Writes metadata to supported audio formats.
    Supports:
        - MP3
        - AIFF
        - WAV
        - FLAC
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(self, track: Track) -> None:
        """
        Convenience method.
        """

        self.rename_file(track)
        self.write_artist(track)
        self.write_title(track)

    def rename_file(self, track: Track) -> None:
        """
        Renames the file to:

            <original_title>.<extension>
        """

        new_path = track.path.with_name(
            f"{track.original_title}{track.extension}"
        )

        if new_path == track.path:
            return

        if new_path.exists():
            raise FileExistsError(
                f"File already exists: {new_path}"
            )

        track.path.rename(new_path)
        track.path = new_path

    def write_artist(self, track: Track) -> None:

        if track.extension == ".flac":
            self._write_flac_artist(track)
        else:
            self._write_id3_artist(track)

    def write_title(self, track: Track) -> None:

        if track.extension == ".flac":
            self._write_flac_title(track)
        else:
            self._write_id3_title(track)

    # ------------------------------------------------------------------
    # FLAC
    # ------------------------------------------------------------------

    def _write_flac_artist(self, track: Track) -> None:

        audio = FLAC(track.path)

        audio["artist"] = track.search_artist

        audio.save()

    def _write_flac_title(self, track: Track) -> None:

        audio = FLAC(track.path)

        audio["title"] = track.original_title

        audio.save()

    # ------------------------------------------------------------------
    # ID3 (MP3 / AIFF / WAV)
    # ------------------------------------------------------------------

    def _write_id3_artist(self, track: Track) -> None:

        audio = File(track.path)

        if audio is None:
            raise RuntimeError(
                f"Unsupported file: {track.path}"
            )

        if audio.tags is None:
            audio.add_tags()

        audio.tags.delall("TPE1")

        audio.tags.add(
            TPE1(
                encoding=3,
                text=[track.search_artist],
            )
        )

        audio.save()

    def _write_id3_title(self, track: Track) -> None:

        audio = File(track.path)

        if audio is None:
            raise RuntimeError(
                f"Unsupported file: {track.path}"
            )

        if audio.tags is None:
            audio.add_tags()

        audio.tags.delall("TIT2")

        audio.tags.add(
            TIT2(
                encoding=3,
                text=[track.original_title],
            )
        )

        audio.save()