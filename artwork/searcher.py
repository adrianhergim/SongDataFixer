"""
searcher.py

Finds artwork for tracks by querying a chain of providers.
"""

from __future__ import annotations

from rapidfuzz import fuzz

from artwork.models import ArtworkCandidate
from artwork.providers.base import ArtworkProvider
from artwork.providers.itunes import ItunesProvider
from artwork.providers.musicbrainz import MusicBrainzProvider
from artwork.providers.placeholder import PlaceholderProvider
from core.models import Track


class ArtworkSearcher:
    """
    Searches providers in priority order, stopping at the first one that
    returns a candidate scoring at or above `min_score`.

    Example
    -------
        searcher = ArtworkSearcher()

        candidate = searcher.search(track)

        if candidate:
            track.artwork_url = candidate.url
            track.provider = candidate.provider
            track.match_score = candidate.score
    """

    def __init__(
        self,
        providers: list[ArtworkProvider] | None = None,
        min_score: float = 30.0,
    ):
        self.providers = providers or [
            ItunesProvider(),
            MusicBrainzProvider(),
            PlaceholderProvider(),
        ]
        self.min_score = min_score

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, track: Track) -> ArtworkCandidate | None:

        for provider in self.providers:

            candidates = provider.search(track)
            best = self._best_match(track, candidates)

            if best is not None and best.score >= self.min_score:
                return best

        return None

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _best_match(
        self,
        track: Track,
        candidates: list[ArtworkCandidate],
    ) -> ArtworkCandidate | None:

        if not candidates:
            return None

        query = self._combined(track.search_artist, track.search_title)

        best = None

        for candidate in candidates:

            candidate.score = fuzz.token_set_ratio(
                query,
                self._combined(candidate.artist, candidate.title),
            )

            if best is None or candidate.score > best.score:
                best = candidate

        return best

    @staticmethod
    def _combined(artist: str, title: str) -> str:
        return f"{artist} {title}".strip().lower()
