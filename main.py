from pathlib import Path

from core.parser import FilenameParser
from core.scanner import MusicScanner
from metadata.writer import MetadataWriter


def main():

    folder = Path(r"C:\PythonScripts\CoverFetch\InputMusic")

    scanner = MusicScanner()
    parser = FilenameParser()
    writer = MetadataWriter()

    for track in scanner.scan(folder):

        parser.parse(track)

        print("=" * 60)
        print(f"File            : {track.filename}")
        print(f"Artist          : {track.search_artist}")
        print(f"Title           : {track.search_title}")
        print(f"Embedded artwork: {track.has_embedded_artwork}")

        writer.write_artist(track)
        writer.write_title(track)
        writer.rename_file(track)

        #print(f"Updated {track.filename}")


if __name__ == "__main__":
    main()