# Image Data Hash

[GitHub](https://github.com/bencevans/image-data-hash) · MIT license · Maintainer: Ben Evans

Native JPEG implementations of ExifTool's `ImageDataHash` in JavaScript,
Python, Rust, R and PHP. MD5 is the default; SHA-256 and SHA-512 are optional.
The libraries do not launch ExifTool or decode pixels.

| Language | Package | Documentation |
| --- | --- | --- |
| TypeScript / JavaScript (Node.js) | `image-data-hash` | [JavaScript README](image-data-hash-js/README.md) |
| Python | `image_data_hash` | [Python README](image-data-hash-py/README.md) |
| Rust | `image_data_hash` | [Rust README](image-data-hash-rs/README.md) |
| R | `imageDataHash` | [R README](image-data-hash-r/README.md) |
| PHP / Composer | `bencevans/image-data-hash` | [PHP README](image-data-hash-php/README.md) |

Each implementation includes installation instructions, API examples, and development commands. See [release checks](PUBLISHING.md) for the publishing workflow.

## Compatibility and scope

Currently supports JPEG only. Hashing follows ExifTool's scan-chunk selection,
including its behavior for progressive JPEGs, byte stuffing, restart markers,
fill bytes and intervening length-bearing segments. See [the byte rules](SPEC.md).

EXIF, IPTC, XMP, ICC profiles and tables before the scans are excluded.
For ordinary baseline JPEGs the hash covers SOS through the byte before EOI.
It is not a decoded-pixel or perceptual hash. MD5 is provided for compatibility;
select SHA-256 or SHA-512 when collision resistance matters.

JavaScript, Python, Rust and PHP offer streaming APIs. R reads one image into memory.
Caller-owned Python/PHP streams stay open; JavaScript closes its input iterator
when hashing finishes. Parsers may read ahead, so streams are not positioned for
reading concatenated JPEGs after a call.

## Tests

Install ExifTool and `cjpeg` (for example, Ubuntu packages
`libimage-exiftool-perl libjpeg-turbo-progs`), then run:

```sh
python3 fixtures/generate.py fixtures/generated
```

The destination must be empty. All five suites require the shared manifest.
CI generates it once and distributes the identical artifact to every language.
The manifest contains ExifTool's MD5, SHA-256 and SHA-512 results for 41 files:
two camera originals, 30 metadata variants, three encoder variants, and six
structural edge cases. Test commands are in each implementation's README.
See [fixture details](fixtures/README.md).
