# Metadata regression fixtures

Install ExifTool and run from the repository root:

```sh
python3 fixtures/generate.py fixtures/generated
```

The destination must be empty. Alternatively, generate into a fresh temporary
directory and export its absolute path as `JPEG_HASH_FIXTURES` before running
the language suites. Generated JPEGs are not committed.

The generator makes 15 variants of each original: timestamp, GPS, orientation,
description, copyright, EXIF species comment, IPTC keywords, XMP subject, large
XMP description (multiple APP1 segments), JPEG comment, EXIF removal, thumbnail
removal and replacement, ignored metadata removal, and combined edits.

`manifest.tsv` assigns every variant its original's fixed SHA-256 content hash.
Expected hashes are never computed with an implementation under test. The
generator requires successful ExifTool execution, checks that each file changed,
and reads back the tags added by the individual edit cases.

All five suites require this manifest and check each variant through both file
and buffer APIs. Existing negative controls also verify that retained APP2 data
changes the hash. CI generates one artifact and passes the identical files and
manifest to all five jobs, so their assertions establish cross-language equality.
