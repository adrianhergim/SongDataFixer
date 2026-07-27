# CoverFetch

Cleans up a messy DJ music library: fixes garbled artist/title tags and fills
in missing cover art, so every track is easy to identify at a glance while
you're mixing.

## What it does

For every audio file in `InputMusic/`:

1. **Scans** the folder recursively for supported audio files (`.mp3`,
   `.flac`, `.wav`, `.aiff`, `.aif`).
2. **Parses** artist/title from the embedded tags and the filename, stripping
   remix/bootleg noise (`(Some DJ Bootleg)`, `Extended Mix`, `FINAL`,
   `MASTER`, track-number prefixes, etc.) down to a clean search query.
3. **Searches for missing cover art**, in order:
   - [iTunes Search API](https://performance-partners.apple.com/search-api)
   - [MusicBrainz](https://musicbrainz.org/) + the
     [Cover Art Archive](https://coverartarchive.org/) (rate-limited to 1
     request/second, per MusicBrainz's usage policy)
   - a generated placeholder — a solid color derived from the track's
     artist/title with the title rendered on top, so every track is at least
     visually distinguishable even when no real cover can be found
4. **Writes back** the cleaned artist/title tags and embeds the artwork
   directly into the file (ID3 `APIC` for MP3/AIFF/WAV, `Picture` block for
   FLAC).

Matching is intentionally loose (default confidence threshold: 30/100) —
the goal is "always have *some* distinguishing artwork for spotting a track
in a DJ set," not archival-grade metadata accuracy.

## Project layout

```
core/               scanning + parsing
    scanner.py          MusicScanner   — recursive audio file discovery
    parser.py            FilenameParser — filename/tag -> clean artist & title
    models.py             Track          — data model passed through the pipeline

artwork/            cover art search
    searcher.py           ArtworkSearcher — tries providers in order, scores matches
    providers/
        base.py               ArtworkProvider interface
        itunes.py             iTunes Search API
        musicbrainz.py        MusicBrainz + Cover Art Archive
        placeholder.py        generated fallback cover

metadata/
    writer.py             MetadataWriter — writes tags, embeds artwork, renames files

InputMusic/          your audio library (input)
artwork_cache/       generated placeholder covers (created on first run)
main.py              entry point — wires the pipeline together
```

## Usage

```
pip install -r requirements.txt
python main.py
```

The folder to process is currently hardcoded in `main.py`
(`InputMusic/` next to it).
