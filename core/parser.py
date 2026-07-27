"""
parser.py

Parses filenames into Track objects.

Examples
--------
50 Cent - In Da Club (Feed The Fire Bootleg).aiff

Original Artist : 50 Cent
Original Title  : In Da Club (Feed The Fire Bootleg)

Search Artist   : 50 Cent
Search Title    : In Da Club
"""

from __future__ import annotations

import re

from mutagen import File
from mutagen.flac import FLAC
from mutagen.id3 import APIC

from core.models import Track


class FilenameParser:

    TITLE_SEPARATORS = (
        " - ",
        " – ",
        " — ",
        "-",
    )

    ARTIST_PATTERNS = (
        r"\bfeat\.?\b",
        r"\bfeaturing\b",
        r"\bft\.?\b",
        r"\bx\b",
        r"&",
        r",",
    )

    DJ_SUFFIXES = (
        "extended mix",
        "original mix",
        "radio edit",
        "club mix",
        "festival mix",
        "festival edit",
        "bootleg",
        "remix",
        "edit",
        "rework",
        "refix",
        "flip",
        "vip",
        "mashup",
        "booty",
        "mix",
    )

    TITLE_SUFFIXES = {
        "FINAL",
        "FINAL2",
        "FINAL3",
        "MASTER",
        "DEMO",
        "TEST",
        "V1",
        "V2",
        "V3",
        "V4",
        "V5",
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, track: Track) -> None:

        artist, title = self._extract(track.stem)

        track.original_artist = artist
        track.original_title = title

        embedded_artist = self._read_metadata(track)

        if embedded_artist:
            track.search_artist = self._clean_artist(embedded_artist)
        else:
            track.search_artist = self._clean_artist(artist)

        track.search_title = self._clean_title(title)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _read_metadata(self, track: Track) -> str:

        audio = File(track.path)

        if audio is None:
            track.has_embedded_artwork = False
            return ""

        track.has_embedded_artwork = self._has_embedded_artwork(audio)

        return self._read_artist(audio)

    def _has_embedded_artwork(self, audio) -> bool:

        # FLAC
        if isinstance(audio, FLAC):
            return len(audio.pictures) > 0

        # MP3 / AIFF / WAV (ID3)
        if audio.tags is None:
            return False

        return any(
            isinstance(frame, APIC)
            for frame in audio.tags.values()
        )

    def _read_artist(self, audio) -> str:

        # FLAC
        if isinstance(audio, FLAC):
            artists = audio.get("artist", [])
            return artists[0] if artists else ""

        # MP3 / AIFF / WAV
        if audio.tags is None:
            return ""

        frame = audio.tags.get("TPE1")

        if frame is None:
            return ""

        if not frame.text:
            return ""

        return frame.text[0]

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    def _extract(self, filename: str) -> tuple[str, str]:

        for separator in self.TITLE_SEPARATORS:

            if separator in filename:

                artist, title = filename.split(separator, 1)

                return artist.strip(), title.strip()

        return "", filename.strip()

    # ------------------------------------------------------------------
    # Artist cleaning
    # ------------------------------------------------------------------

    def _clean_artist(self, artist: str) -> str:

        cleaned = artist

        for pattern in self.ARTIST_PATTERNS:
            cleaned = re.sub(
                pattern,
                " ",
                cleaned,
                flags=re.IGNORECASE,
            )

        cleaned = re.sub(r"\s+", " ", cleaned)

        return cleaned.strip()

    # ------------------------------------------------------------------
    # Title cleaning
    # ------------------------------------------------------------------

    def _clean_title(self, title: str) -> str:

        title = self._remove_brackets(title)
        title = self._remove_dj_suffix(title)
        title = self._remove_suffixes(title)

        title = re.sub(r"\s+", " ", title)

        return title.strip(" -_")

    # ------------------------------------------------------------------

    def _remove_brackets(self, title: str) -> str:
        """
        Remove (...) and [...] completely.

        Example
        -------
        Hello (Bootleg)
        ->
        Hello
        """

        title = re.sub(r"\(.*?\)", "", title)
        title = re.sub(r"\[.*?\]", "", title)

        return title

    # ------------------------------------------------------------------

    def _remove_dj_suffix(self, title: str) -> str:
        """
        Removes trailing remix/edit information.
        """

        words = title.split()

        if not words:
            return title

        for suffix in self.DJ_SUFFIXES:

            suffix_words = suffix.split()

            for i in range(len(words)):

                candidate = " ".join(
                    w.lower()
                    for w in words[i:i + len(suffix_words)]
                )

                if candidate != suffix:
                    continue

                cut = i

                while cut > 0:

                    previous = words[cut - 1]

                    if previous.lower() in {
                        "the",
                        "a",
                        "an",
                        "of",
                        "to",
                        "for",
                        "and",
                        "&",
                    }:
                        break

                    if previous.islower():
                        break

                    cut -= 1

                return " ".join(words[:cut]).strip()

        return title

    # ------------------------------------------------------------------

    def _remove_suffixes(self, title: str) -> str:

        words = title.split()

        while words:

            if words[-1].upper() in self.TITLE_SUFFIXES:
                words.pop()
            else:
                break

        return " ".join(words)