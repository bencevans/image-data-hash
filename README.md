# JPEG Content Hash

A cross-language, metadata-insensitive SHA-256 identifier for JPEG images. Implementations are provided for JavaScript, Python, Rust, R, and PHP.

This is intended for camera-trap collections where annotation software may change EXIF, XMP, IPTC, comments, or appended vendor data without re-encoding the photograph.

## `jpeg_content_sha256_v1`

The canonical byte stream begins with SOI and preserves every JPEG byte in order, except:

- APP1 (`FFE1`): EXIF and XMP
- APP13 (`FFED`): IPTC and Photoshop resources
- COM (`FFFE`): JPEG comments
- all bytes following the first structural EOI (`FFD9`)

APP2 is retained because it commonly contains the ICC colour profile. Other APP segments are also retained because they can affect decoding or contain camera-specific image data. Entropy-coded scan data, byte stuffing, restart markers, tables, dimensions, and encoding parameters are hashed exactly as stored.

The result is the lowercase hexadecimal SHA-256 digest of that canonical stream. A re-encoded or otherwise structurally changed JPEG will normally receive a different hash. This format intentionally supports JPEG only; it does not decode pixels.

## Usage

Python:

```python
from pixel_hash import jpeg_content_sha256
digest = jpeg_content_sha256("fixtures/IMG_0787.JPG")
```

JavaScript (Node.js 18+):

```javascript
import { jpegContentSha256 } from "jpeg-content-hash";
const digest = await jpegContentSha256("fixtures/IMG_0787.JPG");
```

Rust:

```rust
let digest = pixel_hash::jpeg_content_sha256("fixtures/IMG_0787.JPG")?;
```

R (requires `digest`):

```r
source("pixel-hash-r/jpeg_content_sha256.R")
digest <- jpeg_content_sha256("fixtures/IMG_0787.JPG")
```

PHP:

```php
require 'pixel-hash-php/src/JpegContentHash.php';
$digest = jpeg_content_sha256('fixtures/IMG_0787.JPG');
```

Each implementation also exposes an in-memory byte/raw-data function. All suites use the two real camera-trap files in `fixtures/` as shared known-answer vectors, add APP1/APP13/COM metadata, append trailer data, change retained APP2 data, and exercise malformed inputs.

## Streaming

JavaScript, Python, Rust, and PHP path APIs stream automatically. For existing streams/readers use:

- JavaScript: `await jpegContentSha256Stream(readable)`
- Python: `jpeg_content_sha256_stream(binary_file)`
- Rust: `jpeg_content_sha256_reader(reader)`
- PHP: `jpeg_content_sha256_stream($resource)`

JavaScript, Python, Rust, and PHP feed retained chunks directly into SHA-256. R provides `jpeg_content_sha256(path)` and `jpeg_content_sha256_raw(data)` as in-memory APIs: it locates JPEG markers by offset, assembles retained bytes, and hashes them without temporary disk I/O. R's memory usage is proportional to image size, including the canonical copy and parsing allocations; process large collections one image at a time.

## Tests

First install ExifTool and run `python3 fixtures/generate.py fixtures/generated`
from the repository root. Every suite requires the 30 generated metadata
variants and checks the same fixed expected hashes through file and buffer APIs.
See [fixture instructions](fixtures/README.md) for temporary-directory usage.
CI generates these files once and shares them across all five language jobs.

```sh
cd pixel-hash-py && uv run pytest -q
cd pixel-hash-js && npm test
cd pixel-hash-rs && cargo test
cd pixel-hash-r && Rscript -e 'testthat::test_file("test_jpeg_content_sha256.R")'
cd pixel-hash-php && php -d zend.assertions=1 -d assert.exception=1 test.php
```
