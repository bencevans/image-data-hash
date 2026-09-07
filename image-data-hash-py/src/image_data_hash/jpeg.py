"""Native JPEG image-data hashing compatible with ExifTool.

Metadata and tables before scans are skipped. Each scan chunk is tentatively
hashed until the following marker determines whether ExifTool includes it.
"""

import hashlib
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Protocol

MARKER_PREFIX = 0xFF
START_OF_SCAN = 0xDA
END_OF_IMAGE = 0xD9
BUFFER_SIZE = 65536


class _Digest(Protocol):
    """Operations shared by hashlib's MD5 and SHA implementations."""

    def update(self, data: bytes) -> None: ...
    def copy(self) -> "_Digest": ...
    def hexdigest(self) -> str: ...


def _normalize_algorithm(name: str) -> str:
    """Accept the three ExifTool algorithms, ignoring case and hyphens."""
    normalized = name.lower().replace("-", "")
    if normalized not in ("md5", "sha256", "sha512"):
        raise ValueError("algorithm must be MD5, SHA-256 or SHA-512")
    return normalized


def _has_length_field(marker: int) -> bool:
    """ExifTool treats SOS as lengthless so its header joins the scan bytes."""
    return not (marker in (0, 1) or 0xD0 <= marker <= 0xDA)


def _starts_hash_chunk(marker: int) -> bool:
    """SOS, escaped FF bytes and restart markers start candidate chunks."""
    return marker in (0, START_OF_SCAN) or 0xD0 <= marker <= 0xD7


class _BufferedInput:
    """Buffer small reads while supporting non-seekable binary streams."""

    def __init__(self, source: BinaryIO):
        self.source = source
        self.buffer = b""
        self.position = 0

    def _ensure_data(self) -> None:
        if self.position < len(self.buffer):
            return
        self.buffer = self.source.read(BUFFER_SIZE)
        self.position = 0
        if not isinstance(self.buffer, bytes):
            raise TypeError("source must yield bytes")
        if not self.buffer:
            raise ValueError("truncated JPEG or missing end-of-image marker")

    def read_exact(self, size: int) -> bytes:
        """Read a small header or segment, raising on premature EOF."""
        parts = []
        remaining = size
        while remaining > 0:
            self._ensure_data()
            count = min(remaining, len(self.buffer) - self.position)
            parts.append(self.buffer[self.position : self.position + count])
            self.position += count
            remaining -= count
        return b"".join(parts)

    def read_marker(self, pending_digest: _Digest | None) -> tuple[int, int]:
        """Hash ordinary bytes, then return the next marker and FF fill count.

        The first FF ends the ordinary data. Additional FF bytes are delayed
        until the marker code tells us whether to keep the candidate digest.
        """
        while True:
            self._ensure_data()
            marker_position = self.buffer.find(b"\xff", self.position)
            end = len(self.buffer) if marker_position < 0 else marker_position
            if pending_digest is not None:
                pending_digest.update(self.buffer[self.position : end])
            self.position = end
            if marker_position >= 0:
                self.position += 1
                break

        fill_count = 0
        marker = self.read_exact(1)[0]
        while marker == MARKER_PREFIX:
            fill_count += 1
            marker = self.read_exact(1)[0]
        return marker, fill_count


def image_data_hash_stream(source: BinaryIO, algorithm: str = "md5") -> str:
    """Hash a blocking binary JPEG stream using bounded working memory.

    Args:
        source: Open binary stream with a read(size) method. It stays open.
            Reads may consume data beyond EOI; do not rely on the final position.
        algorithm: MD5 (default), SHA-256 or SHA-512, case-insensitive.

    Returns:
        Lowercase hexadecimal digest of 32, 64 or 128 characters.

    Raises:
        ValueError: Unsupported algorithm or malformed/truncated JPEG.
        TypeError: The stream returns text instead of bytes.
        OSError: The underlying stream cannot be read.
    """
    digest = hashlib.new(_normalize_algorithm(algorithm))
    reader = _BufferedInput(source)
    if reader.read_exact(2) != b"\xff\xd8":
        raise ValueError("not a JPEG file")

    pending_digest = None
    found_scan = False

    while True:
        marker, fill_count = reader.read_marker(pending_digest)

        # ExifTool includes the preceding chunk only before a lengthless marker.
        # Copying the digest allows us to discard a chunk without buffering it.
        if pending_digest is not None and not _has_length_field(marker):
            while fill_count > 0:
                count = min(fill_count, BUFFER_SIZE)
                pending_digest.update(b"\xff" * count)
                fill_count -= count
            digest = pending_digest
        pending_digest = None

        if marker == END_OF_IMAGE:
            if not found_scan:
                raise ValueError("JPEG has no start-of-scan marker")
            return digest.hexdigest()

        if marker == START_OF_SCAN:
            found_scan = True
        if _starts_hash_chunk(marker):
            pending_digest = digest.copy()
            pending_digest.update(bytes((MARKER_PREFIX, marker)))

        if _has_length_field(marker):
            segment_length = int.from_bytes(reader.read_exact(2), "big")
            if segment_length < 2:
                raise ValueError("invalid JPEG segment length")
            # JPEG segment lengths include their own two-byte length field.
            reader.read_exact(segment_length - 2)


def image_data_hash_bytes(data: bytes, algorithm: str = "md5") -> str:
    """Hash complete JPEG bytes and return a lowercase hexadecimal digest.

    algorithm accepts MD5 (default), SHA-256 or SHA-512. Data after EOI is
    ignored. Raises ValueError for invalid JPEGs or unsupported algorithms.
    """
    return image_data_hash_stream(BytesIO(data), algorithm)


def image_data_hash(source: str | Path | BinaryIO, algorithm: str = "md5") -> str:
    """Hash a JPEG path or open binary stream, defaulting to MD5.

    Returns a lowercase hexadecimal string. Files opened by this function are
    closed on completion; caller-owned streams remain open. Raises ValueError
    for malformed input or unsupported algorithms, and OSError for I/O failures.
    """
    if hasattr(source, "read"):
        return image_data_hash_stream(source, algorithm)
    with Path(source).open("rb") as stream:
        return image_data_hash_stream(stream, algorithm)
