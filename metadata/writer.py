"""
writer.py

Renames audio files and writes metadata.
"""

from __future__ import annotations

import httpx
from mutagen import File
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, TIT2, TPE1

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

    COVER_TYPE = 3  # ID3 / FLAC "front cover" picture type

    def __init__(self, client: httpx.Client | None = None):
        self.client = client or httpx.Client(timeout=10.0)

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
        self.write_artwork(track)

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

    def write_artwork(self, track: Track) -> None:

        image_data, mime = self._load_artwork(track)

        if image_data is None:
            return

        if track.extension == ".flac":
            self._write_flac_artwork(track, image_data, mime)
        else:
            self._write_id3_artwork(track, image_data, mime)

    # ------------------------------------------------------------------
    # Artwork loading
    # ------------------------------------------------------------------

    def _load_artwork(self, track: Track) -> tuple[bytes | None, str]:

        if track.artwork_path is not None:
            return track.artwork_path.read_bytes(), "image/png"

        if not track.artwork_url:
            return None, ""

        try:
            response = self.client.get(track.artwork_url)
            response.raise_for_status()
        except httpx.HTTPError:
            return None, ""

        mime = response.headers.get("content-type", "image/jpeg").split(";")[0].strip()

        return response.content, mime

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

    def _write_flac_artwork(self, track: Track, data: bytes, mime: str) -> None:

        audio = FLAC(track.path)

        picture = Picture()
        picture.type = self.COVER_TYPE
        picture.mime = mime
        picture.data = data

        audio.clear_pictures()
        audio.add_picture(picture)

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

    def _write_id3_artwork(self, track: Track, data: bytes, mime: str) -> None:

        audio = File(track.path)

        if audio is None:
            raise RuntimeError(
                f"Unsupported file: {track.path}"
            )

        if audio.tags is None:
            audio.add_tags()

        audio.tags.delall("APIC")

        audio.tags.add(
            APIC(
                encoding=3,
                mime=mime,
                type=self.COVER_TYPE,
                desc="Cover",
                data=data,
            )
        )

        audio.save()