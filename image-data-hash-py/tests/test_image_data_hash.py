import csv
import os
from io import BytesIO
from pathlib import Path

import pytest

from image_data_hash import (
    image_data_hash,
    image_data_hash_bytes,
    image_data_hash_stream,
)

DIRECTORY = Path(
    os.environ.get(
        "JPEG_HASH_FIXTURES", str(Path(__file__).parents[2] / "fixtures/generated")
    )
)
with (DIRECTORY / "manifest.tsv").open() as manifest:
    VECTORS = list(csv.DictReader(manifest, delimiter="\t"))
assert len(VECTORS) == 41, "Generate all compatibility fixtures before testing"


@pytest.mark.parametrize("row", VECTORS, ids=lambda row: row["file"])
@pytest.mark.parametrize("algorithm", ["md5", "sha256", "sha512"])
def test_matches_exiftool(row, algorithm):
    path = DIRECTORY / row["file"]
    assert image_data_hash(path, algorithm) == row[algorithm]
    assert image_data_hash_bytes(path.read_bytes(), algorithm) == row[algorithm]


def test_default_and_algorithm_aliases():
    path = DIRECTORY / VECTORS[0]["file"]
    assert image_data_hash(path) == VECTORS[0]["md5"]
    assert image_data_hash(path, "SHA-256") == VECTORS[0]["sha256"]
    assert image_data_hash(path, "SHA-512") == VECTORS[0]["sha512"]
    with pytest.raises(ValueError):
        image_data_hash(path, "sha1")


class ShortReader(BytesIO):
    def read(self, size=-1):
        return super().read(min(size, 1))


@pytest.mark.parametrize(
    "row", [row for row in VECTORS if row["file"].startswith("structural")]
)
def test_split_markers(row):
    source = ShortReader((DIRECTORY / row["file"]).read_bytes())
    assert image_data_hash_stream(source) == row["md5"]
    assert not source.closed


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"not jpeg",
        b"\xff\xd8",
        b"\xff\xd8\xff\xe1\x00",
        b"\xff\xd8\xff\xe1\x00\x01",
        b"\xff\xd8\xff\xd9",
        b"\xff\xd8\xff\xda\x00\x02abc\xff",
    ],
)
def test_invalid_input(data):
    with pytest.raises(ValueError):
        image_data_hash_bytes(data)
