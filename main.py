from pathlib import Path

from artwork.searcher import ArtworkSearcher
from core.parser import FilenameParser
from core.scanner import MusicScanner
from metadata.writer import MetadataWriter


ARTIST_MATCH_THRESHOLD = 80.0


def main():

    folder = Path(r"C:\PythonScripts\CoverFetch\InputMusic")

    scanner = MusicScanner()
    parser = FilenameParser()
    searcher = ArtworkSearcher()
    writer = MetadataWriter()

    for track in scanner.scan(folder):

        parser.parse(track)

        needs_artwork = not track.has_embedded_artwork
        needs_artist = not track.search_artist

        if needs_artwork or needs_artist:

            candidate = searcher.search(track)

            if candidate:

                if needs_artwork:
                    track.artwork_url = candidate.url
                    track.artwork_path = candidate.local_path
                    track.provider = candidate.provider
                    track.match_score = candidate.score

                if (
                    needs_artist
                    and candidate.provider != "placeholder"
                    and candidate.score >= ARTIST_MATCH_THRESHOLD
                ):
                    track.search_artist = parser.clean_artist(candidate.artist)

        print("=" * 60)
        print(f"File            : {track.filename}")
        print(f"Artist          : {track.search_artist}")
        print(f"Title           : {track.search_title}")
        print(f"Embedded artwork: {track.has_embedded_artwork}")

        if needs_artwork:
            print(f"Artwork match   : {track.provider or 'none'} ({track.match_score:.0f})")

        writer.write_artist(track)
        writer.write_title(track)

        if needs_artwork:
            writer.write_artwork(track)

        writer.rename_file(track)

        #print(f"Updated {track.filename}")


if __name__ == "__main__":
    main()