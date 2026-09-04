from pathlib import Path
import os
import csv
import pytest
from pixel_hash import jpeg_content_sha256, jpeg_content_sha256_bytes, jpeg_content_sha256_stream

FIXTURES = Path(__file__).parents[2] / "fixtures"
VECTORS = {
    "IMG_0787.JPG": "fdc79d5549c0fa9190c422afc9ae506964904a328ff5c67ef6298cd5ead8e6b7",
    "IMG_1039.JPG": "8cb0c2dfb0fb6a2bb7ecd28555dd49ada047b2bb45c53be4aeea7d56edc86b9d",
}


def test_generated_exif_variants():
    directory = Path(os.environ.get("JPEG_HASH_FIXTURES", str(FIXTURES / "generated")))
    with (directory / "manifest.tsv").open() as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    assert len(rows) == 30
    for row in rows:
        path = directory / row["file"]
        assert jpeg_content_sha256(path) == row["sha256"], row["file"]
        assert jpeg_content_sha256_bytes(path.read_bytes()) == row["sha256"], row["file"]


def segment(marker: int, payload: bytes) -> bytes:
    return b"\xff" + bytes([marker]) + (len(payload) + 2).to_bytes(2, "big") + payload


@pytest.mark.parametrize("name,expected", VECTORS.items())
def test_known_hash(name, expected):
    assert jpeg_content_sha256(FIXTURES / name) == expected


def test_ignored_metadata_does_not_change_hash():
    for name, expected in VECTORS.items():
        original = (FIXTURES / name).read_bytes()
        for marker in (0xE1, 0xED, 0xFE):
            assert jpeg_content_sha256_bytes(original[:2] + segment(marker, b"changed metadata") + original[2:]) == expected
        assert jpeg_content_sha256_bytes(original + b"vendor trailer") == expected


def test_retained_segment_changes_hash():
    original = (FIXTURES / "IMG_0787.JPG").read_bytes()
    modified = original[:2] + segment(0xE2, b"ICC profile") + original[2:]
    assert jpeg_content_sha256_bytes(modified) != jpeg_content_sha256_bytes(original)


def test_streaming_handles_one_byte_reads():
    class OneByteReader:
        def __init__(self, data): self.data, self.offset = data, 0
        def read(self, _size=-1):
            if self.offset == len(self.data): return b""
            value = self.data[self.offset : self.offset + 1]; self.offset += 1; return value
    data = (FIXTURES / "IMG_0787.JPG").read_bytes()
    assert jpeg_content_sha256_stream(OneByteReader(data)) == VECTORS["IMG_0787.JPG"]


@pytest.mark.parametrize("data", [b"", b"not jpeg", b"\xff\xd8", b"\xff\xd8\xff\xe1\x00"])
def test_invalid_input(data):
    with pytest.raises(ValueError):
        jpeg_content_sha256_bytes(data)
