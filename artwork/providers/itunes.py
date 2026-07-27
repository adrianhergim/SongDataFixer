"""
itunes.py

Artwork provider backed by the iTunes Search API.
"""

from __future__ import annotations

import httpx

from artwork.models import ArtworkCandidate
from artwork.providers.base import ArtworkProvider
from core.models import Track


class ItunesProvider(ArtworkProvider):
    """
    Looks up artwork via the iTunes Search API.

    https://performance-partners.apple.com/search-api
    """

    name = "itunes"

    SEARCH_URL = "https://itunes.apple.com/search"
    ARTWORK_SIZE = "600x600"

    def __init__(
        self,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
    ):
        self.client = client or httpx.Client(timeout=timeout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, track: Track) -> list[ArtworkCandidate]:

        params = {
            "term": f"{track.search_artist} {track.search_title}",
            "media": "music",
            "entity": "song",
            "limit": 10,
        }

        try:
            response = self.client.get(self.SEARCH_URL, params=params)
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        results = response.json().get("results", [])

        candidates = []

        for result in results:

            candidate = self._to_candidate(result)

            if candidate is not None:
                candidates.append(candidate)

        return candidates

    # ------------------------------------------------------------------

    def _to_candidate(self, result: dict) -> ArtworkCandidate | None:

        artwork_url = result.get("artworkUrl100")

        if not artwork_url:
            return None

        return ArtworkCandidate(
            url=artwork_url.replace("100x100", self.ARTWORK_SIZE),
            provider=self.name,
            artist=result.get("artistName", ""),
            title=result.get("trackName", ""),
            album=result.get("collectionName", ""),
        )
