from pathlib import Path

from artwork.searcher import ArtworkSearcher
from core.parser import FilenameParser
from core.scanner import MusicScanner
from metadata.writer import MetadataWriter


def main():

    folder = Path(r"C:\PythonScripts\CoverFetch\InputMusic")

    scanner = MusicScanner()
    parser = FilenameParser()
    searcher = ArtworkSearcher()
    writer = MetadataWriter()

    for track in scanner.scan(folder):

        parser.parse(track)

        if not track.has_embedded_artwork:

            candidate = searcher.search(track)

            if candidate:
                track.artwork_url = candidate.url
                track.artwork_path = candidate.local_path
                track.provider = candidate.provider
                track.match_score = candidate.score

        print("=" * 60)
        print(f"File            : {track.filename}")
        print(f"Artist          : {track.search_artist}")
        print(f"Title           : {track.search_title}")
        print(f"Embedded artwork: {track.has_embedded_artwork}")

        if not track.has_embedded_artwork:
            print(f"Artwork match   : {track.provider or 'none'} ({track.match_score:.0f})")

        writer.write_artist(track)
        writer.write_title(track)

        if not track.has_embedded_artwork:
            writer.write_artwork(track)

        writer.rename_file(track)

        #print(f"Updated {track.filename}")


if __name__ == "__main__":
    main()