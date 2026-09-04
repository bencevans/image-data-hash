"""Streaming implementation of the jpeg_content_sha256_v1 format."""

from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

_IGNORED = {0xE1, 0xED, 0xFE}


def _read_exact(source: BinaryIO, size: int) -> bytes:
    parts: list[bytes] = []
    remaining = size
    while remaining:
        part = source.read(remaining)
        if not part:
            raise ValueError("truncated JPEG segment")
        if not isinstance(part, bytes):
            raise TypeError("source must yield bytes")
        parts.append(part)
        remaining -= len(part)
    return b"".join(parts)


def jpeg_content_sha256_stream(source: BinaryIO) -> str:
    """Hash a binary stream using bounded memory, stopping at the first JPEG EOI."""
    digest = sha256()
    soi = _read_exact(source, 2)
    if soi != b"\xff\xd8":
        raise ValueError("not a JPEG file")
    digest.update(soi)
    in_scan = False
    scan_buffer = bytearray()
    pending_marker: bytes | None = None

    def flush_scan() -> None:
        if scan_buffer:
            digest.update(scan_buffer)
            scan_buffer.clear()

    while True:
        if in_scan and pending_marker is None:
            byte = source.read(1)
            if not byte:
                raise ValueError("JPEG has no EOI marker")
            if byte != b"\xff":
                scan_buffer.extend(byte)
                if len(scan_buffer) >= 65536:
                    flush_scan()
                continue
            marker = bytearray(byte)
            while True:
                code = source.read(1)
                if not code:
                    raise ValueError("truncated JPEG marker")
                marker.extend(code)
                if code != b"\xff":
                    break
            value = code[0]
            if value == 0x00 or 0xD0 <= value <= 0xD7:
                scan_buffer.extend(marker)
                continue
            flush_scan()
            in_scan = False
            pending_marker = bytes(marker)

        if pending_marker is None:
            first = source.read(1)
            if not first:
                raise ValueError("JPEG has no EOI marker")
            if first != b"\xff":
                raise ValueError("unexpected data outside JPEG scan")
            marker = bytearray(first)
            while True:
                code = source.read(1)
                if not code:
                    raise ValueError("truncated JPEG marker")
                marker.extend(code)
                if code != b"\xff":
                    break
            marker_bytes = bytes(marker)
        else:
            marker_bytes = pending_marker
            code = marker_bytes[-1:]
            pending_marker = None

        value = code[0]
        if value == 0xD9:
            digest.update(marker_bytes)
            return digest.hexdigest()
        if value == 0x01 or 0xD0 <= value <= 0xD8:
            digest.update(marker_bytes)
            continue

        length_bytes = _read_exact(source, 2)
        length = int.from_bytes(length_bytes, "big")
        if length < 2:
            raise ValueError("invalid JPEG segment length")
        retained = value not in _IGNORED
        if retained:
            digest.update(marker_bytes)
            digest.update(length_bytes)
        remaining = length - 2
        while remaining:
            part = _read_exact(source, min(remaining, 65536))
            if retained:
                digest.update(part)
            remaining -= len(part)
        in_scan = value == 0xDA


def jpeg_content_sha256_bytes(data: bytes) -> str:
    """Hash JPEG bytes without creating a second canonical copy."""
    return jpeg_content_sha256_stream(BytesIO(data))


def jpeg_content_sha256(source: str | Path | BinaryIO) -> str:
    """Hash a JPEG path or an already-open binary stream."""
    if hasattr(source, "read"):
        return jpeg_content_sha256_stream(source)
    with Path(source).open("rb") as stream:
        return jpeg_content_sha256_stream(stream)
