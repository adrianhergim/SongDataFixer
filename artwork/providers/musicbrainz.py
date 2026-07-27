"""
musicbrainz.py

Artwork provider backed by MusicBrainz recording search + the Cover Art
Archive.
"""

from __future__ import annotations

import time

import httpx
import musicbrainzngs

from artwork.models import ArtworkCandidate
from artwork.providers.base import ArtworkProvider
from core.models import Track

musicbrainzngs.set_useragent(
    "CoverFetch",
    "0.1",
    "https://github.com/placeholder/coverfetch",
)


class MusicBrainzProvider(ArtworkProvider):
    """
    Looks up artwork via MusicBrainz recording search, then resolves cover
    art through the Cover Art Archive.

    MusicBrainz asks clients to send at most one request per second, so this
    provider throttles its own MusicBrainz calls. To keep the total request
    count (and wait time) bounded, only the first release of each recording
    match is checked against the Cover Art Archive.
    """

    name = "musicbrainz"

    COVER_ART_URL = "https://coverartarchive.org/release/{mbid}"
    MIN_REQUEST_INTERVAL = 1.0
    RECORDING_LIMIT = 5

    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
    ):
        self.client = client or httpx.Client(timeout=timeout)
        self._last_request_at = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, track: Track) -> list[ArtworkCandidate]:

        recordings = self._search_recordings(track)

        candidates = []

        for recording in recordings:

            candidate = self._to_candidate(recording)

            if candidate is not None:
                candidates.append(candidate)

        return candidates

    # ------------------------------------------------------------------
    # MusicBrainz
    # ------------------------------------------------------------------

    def _search_recordings(self, track: Track) -> list[dict]:

        self._throttle()

        try:
            result = musicbrainzngs.search_recordings(
                artist=track.search_artist,
                recording=track.search_title,
                limit=self.RECORDING_LIMIT,
            )
        except musicbrainzngs.WebServiceError:
            return []

        return result.get("recording-list", [])

    def _artist_credit(self, recording: dict) -> str:

        names = []

        for credit in recording.get("artist-credit", []):

            if not isinstance(credit, dict):
                continue

            name = credit.get("artist", {}).get("name", "")

            if name:
                names.append(name)

        return " ".join(names)

    def _throttle(self) -> None:

        elapsed = time.monotonic() - self._last_request_at
        remaining = self.MIN_REQUEST_INTERVAL - elapsed

        if remaining > 0:
            time.sleep(remaining)

        self._last_request_at = time.monotonic()

    # ------------------------------------------------------------------
    # Cover Art Archive
    # ------------------------------------------------------------------

    def _to_candidate(self, recording: dict) -> ArtworkCandidate | None:

        releases = recording.get("release-list", [])

        if not releases:
            return None

        release = releases[0]
        mbid = release.get("id")

        if not mbid:
            return None

        artwork_url = self._fetch_cover_url(mbid)

        if artwork_url is None:
            return None

        return ArtworkCandidate(
            url=artwork_url,
            provider=self.name,
            artist=self._artist_credit(recording),
            title=recording.get("title", ""),
            album=release.get("title", ""),
        )

    def _fetch_cover_url(self, mbid: str) -> str | None:

        url = self.COVER_ART_URL.format(mbid=mbid)

        try:
            response = self.client.get(url)
        except httpx.HTTPError:
            return None

        if response.status_code != 200:
            return None

        for image in response.json().get("images", []):

            if image.get("front"):
                return image.get("image")

        return None
