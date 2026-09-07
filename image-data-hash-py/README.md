# image_data_hash for Python

Native JPEG ImageDataHash matching ExifTool. Python 3.10+; no runtime dependencies.
Distribution and import name: `image_data_hash`.

## Installation

```sh
python3 -m pip install image_data_hash
```

## Usage

```python
from image_data_hash import image_data_hash, image_data_hash_bytes, image_data_hash_stream

digest = image_data_hash("photo.jpg")  # MD5 by default
digest = image_data_hash("photo.jpg", algorithm="sha256")
digest = image_data_hash("photo.jpg", algorithm="sha512")

with open("photo.jpg", "rb") as source:
    digest = image_data_hash_stream(source, algorithm="sha256")

digest = image_data_hash_bytes(jpeg_bytes, algorithm="sha256")
```

Names such as `MD5`, `SHA-256` and `SHA-512` are accepted. Returns lowercase
hexadecimal. Path calls close their files; stream calls leave caller-owned streams
open. Streams must provide blocking binary reads. Hashing uses bounded working
memory; the buffer helper retains the input in memory. Invalid/truncated JPEGs
raise `ValueError`; file errors propagate.

## Tests

Generate the [shared fixtures](https://github.com/bencevans/image-data-hash/blob/main/fixtures/README.md) first, then:

```sh
cd image-data-hash-py
uv sync --locked
uv run black --check src tests
uv run pytest -q
```

Tests compare both file and bytes APIs against ExifTool for all three algorithms,
including one-byte reads. See [compatibility rules](https://github.com/bencevans/image-data-hash/blob/main/SPEC.md).

## Project

Repository: [bencevans/image-data-hash](https://github.com/bencevans/image-data-hash). Maintainer: Ben Evans. Licensed under MIT.
