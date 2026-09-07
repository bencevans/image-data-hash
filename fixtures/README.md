# Compatibility fixtures

Install ExifTool and `cjpeg`, then run from the repository root:

```sh
python3 fixtures/generate.py fixtures/generated
```

The destination must be empty. To use a temporary directory, export its absolute
path as `JPEG_HASH_FIXTURES` before running any suite. Generated JPEGs are ignored
by Git. The two original photographs are never modified.

The 41 fixtures include:

- Two original camera-trap photographs.
- Fifteen metadata variants per original: timestamp, GPS, orientation,
  description, copyright, EXIF species comment, IPTC keywords, XMP subject,
  large XMP description, JPEG comment, EXIF removal, thumbnail removal and
  replacement, ignored-metadata removal, and combined edits.
- Baseline, progressive and restart-marker JPEGs encoded from deterministic pixels.
- Six structural vectors covering stuffing, restarts, fill bytes, multiple scans,
  intervening comments and changed scan bytes. These test the parser and need not
  be decodable photographs.

ExifTool generates all expected hashes in `manifest.tsv` (columns `file`,
`md5`, `sha256`, `sha512`). The generator verifies that metadata edits retain
the original hashes, and records `exiftool-version.txt`. No implementation under
test is used to calculate expected values.

Every language suite requires all 41 entries and checks each algorithm through
file and buffer APIs. CI generates one artifact and shares it across the five jobs.
