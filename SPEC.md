# JPEG ImageDataHash compatibility

The compatibility target is ExifTool's `ImageDataHash` with `ImageHashType`
set to MD5 (default), SHA256, or SHA512. Outputs are lowercase hexadecimal
strings of 32, 64, or 128 characters. String-based APIs accept case-insensitive
names with or without hyphens; other algorithms are rejected.

## Byte selection

The parser requires SOI (`FF D8`). For JPEG hashing, ExifTool treats SOS
(`FF DA`) as a marker without a length field: the SOS header bytes are read
as part of the following scan chunk.

A candidate chunk starts with the two-byte marker for SOS, a stuffed zero
(`FF 00`), or a restart (`FF D0` through `FF D7`). It extends through the
bytes before the next marker. Repeated FF fill bytes belong to the preceding
chunk except for the final FF, which is the next marker's prefix.

The candidate contributes to the hash only when the next marker has no
length field. If the next marker has a length field, the candidate is discarded
and that segment is skipped. This follows ExifTool's implementation, including
its less intuitive behavior between progressive scans. It is not equivalent
to hashing every byte between the first SOS and EOI in all JPEGs.

For the supported JPEG markers, the markers without lengths are `00`, `01`,
and `D0` through `DA`. Hashing ends at EOI (`FF D9`), which is excluded.
Trailers and embedded thumbnails outside these chunks are excluded.

The native streaming implementations keep a tentative digest for each candidate,
committing or discarding it once the next marker is known. This avoids buffering
an entire scan. R instead selects byte ranges in memory.

## Input limitations

JPEG only; this does not implement ExifTool's rules for TIFF, PNG, RAW or video.
Truncated marker/segment input and files without SOS/EOI are rejected. This is
a hashing parser, not a full JPEG decoder or conformance validator. Error
recovery for malformed files is not intended to match ExifTool.

## Verification

The fixture generator records the installed ExifTool version and uses that
executable as the oracle for all three algorithms. The library code never
invokes it. Tests include real progressive and restart-marker JPEGs alongside
the camera-trap metadata variants. Hash compatibility is tested against these
fixtures; it is not a claim about every undocumented ExifTool behavior.

Reference: [ExifTool JPEG parser](https://github.com/exiftool/exiftool/blob/master/lib/Image/ExifTool.pm)
and [ImageHashType options](https://exiftool.org/ExifTool.html#ImageHashType).
