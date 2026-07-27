"""
base.py

Common interface every artwork provider implements.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from artwork.models import ArtworkCandidate
from core.models import Track


class ArtworkProvider(ABC):
    """
    Looks up artwork for a track on a single external source.
    """

    name: str

    @abstractmethod
    def search(self, track: Track) -> list[ArtworkCandidate]:
        """
        Returns raw candidates for the track.

        No scoring or filtering — that is the searcher's job.
        """
