"""
placeholder.py

Fallback artwork provider that generates a simple cover locally instead of
searching an external source.
"""

from __future__ import annotations

import colorsys
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from artwork.models import ArtworkCandidate
from artwork.providers.base import ArtworkProvider
from core.models import Track


class PlaceholderProvider(ArtworkProvider):
    """
    Generates a deterministic placeholder cover from the track's artist and
    title, so every track ends up with at least some distinguishable
    artwork when no real provider finds a match.

    The same artist/title always renders the same color and is cached on
    disk, so this never hits the network and is safe to use as the last
    entry in a provider chain.
    """

    name = "placeholder"

    SIZE = 600
    CACHE_DIR = Path("artwork_cache")

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or self.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, track: Track) -> list[ArtworkCandidate]:

        image_path = self._image_path(track)

        if not image_path.exists():
            self._render(track, image_path)

        return [
            ArtworkCandidate(
                provider=self.name,
                artist=track.search_artist,
                title=track.search_title,
                local_path=image_path,
            )
        ]

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _image_path(self, track: Track) -> Path:

        digest = self._digest(track)

        return self.cache_dir / f"{digest.hex()[:16]}.png"

    def _render(self, track: Track, image_path: Path) -> None:

        image = Image.new("RGB", (self.SIZE, self.SIZE), self._color_for(track))
        draw = ImageDraw.Draw(image)

        text = track.search_title or track.search_artist or "Unknown"
        font = ImageFont.load_default(size=48)

        lines = self._wrap(draw, text, font, max_width=self.SIZE - 80)
        line_height = draw.textbbox((0, 0), "Ag", font=font)[3]
        total_height = line_height * len(lines)

        y = (self.SIZE - total_height) / 2

        for line in lines:

            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (self.SIZE - line_width) / 2

            draw.text((x, y), line, fill="white", font=font)

            y += line_height

        image.save(image_path)

    def _wrap(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont,
        max_width: int,
    ) -> list[str]:

        words = text.split()
        lines = []
        current = ""

        for word in words:

            candidate = f"{current} {word}".strip()
            width = draw.textbbox((0, 0), candidate, font=font)[2]

            if width <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines

    def _color_for(self, track: Track) -> tuple[int, int, int]:

        digest = self._digest(track)
        hue = digest[0] / 255

        red, green, blue = colorsys.hsv_to_rgb(hue, 0.55, 0.85)

        return (int(red * 255), int(green * 255), int(blue * 255))

    def _digest(self, track: Track) -> bytes:

        key = f"{track.search_artist}|{track.search_title}".lower()

        return hashlib.sha1(key.encode("utf-8")).digest()
