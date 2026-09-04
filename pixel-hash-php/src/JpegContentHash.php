<?php

declare(strict_types=1);

function canonical_jpeg(string $data): string
{
    $size = strlen($data);
    if ($size < 4 || substr($data, 0, 2) !== "\xff\xd8") throw new InvalidArgumentException('not a JPEG file');
    $out = substr($data, 0, 2);
    $pos = 2; $inScan = false; $scanStart = 0;
    while ($pos < $size) {
        $markerStart = $pos;
        if (ord($data[$pos]) !== 0xff) {
            if (!$inScan) throw new InvalidArgumentException("unexpected data at offset $pos");
            ++$pos; continue;
        }
        while ($pos < $size && ord($data[$pos]) === 0xff) ++$pos;
        if ($pos === $size) throw new InvalidArgumentException('truncated JPEG marker');
        $marker = ord($data[$pos++]);
        if ($inScan && $marker === 0x00) continue;
        if ($inScan && $marker >= 0xd0 && $marker <= 0xd7) continue;
        if ($inScan) { $out .= substr($data, $scanStart, $markerStart - $scanStart); $inScan = false; }
        if ($marker === 0xd9) {
            $out .= substr($data, $markerStart, $pos - $markerStart);
            return $out;
        }
        if ($marker === 0x01 || ($marker >= 0xd0 && $marker <= 0xd8)) {
            $out .= substr($data, $markerStart, $pos - $markerStart); continue;
        }
        if ($pos + 2 > $size) throw new InvalidArgumentException('truncated JPEG segment length');
        $length = unpack('n', substr($data, $pos, 2))[1];
        if ($length < 2 || $pos + $length > $size) throw new InvalidArgumentException('invalid or truncated JPEG segment');
        $end = $pos + $length;
        if (!in_array($marker, [0xe1, 0xed, 0xfe], true)) $out .= substr($data, $markerStart, $end - $markerStart);
        $pos = $end; $inScan = $marker === 0xda;
        if ($inScan) $scanStart = $pos;
    }
    throw new InvalidArgumentException('JPEG has no EOI marker');
}

function jpeg_content_sha256_bytes(string $data): string
{
    $stream = fopen('php://memory', 'w+b');
    fwrite($stream, $data); rewind($stream);
    try { return jpeg_content_sha256_stream($stream); } finally { fclose($stream); }
}

/** @param resource $stream */
function jpeg_content_sha256_stream($stream): string
{
    if (!is_resource($stream)) throw new InvalidArgumentException('stream must be a readable resource');
    $readExact = function (int $length) use ($stream): string {
        $result = '';
        while (strlen($result) < $length) {
            $part = fread($stream, $length - strlen($result));
            if ($part === false || $part === '') throw new InvalidArgumentException('truncated JPEG segment');
            $result .= $part;
        }
        return $result;
    };
    $context = hash_init('sha256');
    $soi = $readExact(2);
    if ($soi !== "\xff\xd8") throw new InvalidArgumentException('not a JPEG file');
    hash_update($context, $soi);
    $inScan = false; $pending = null; $scan = '';
    while (true) {
        if ($inScan && $pending === null) {
            $value = $readExact(1);
            if ($value !== "\xff") {
                $scan .= $value;
                if (strlen($scan) >= 65536) { hash_update($context, $scan); $scan = ''; }
                continue;
            }
            $marker = $value;
            do { $codeByte = $readExact(1); $marker .= $codeByte; } while ($codeByte === "\xff");
            $code = ord($codeByte);
            if ($code === 0 || ($code >= 0xd0 && $code <= 0xd7)) { $scan .= $marker; continue; }
            if ($scan !== '') { hash_update($context, $scan); $scan = ''; }
            $inScan = false; $pending = $marker;
        }
        if ($pending !== null) { $marker = $pending; $pending = null; }
        else {
            if ($readExact(1) !== "\xff") throw new InvalidArgumentException('unexpected data outside JPEG scan');
            $marker = "\xff";
            do { $codeByte = $readExact(1); $marker .= $codeByte; } while ($codeByte === "\xff");
        }
        $code = ord($marker[strlen($marker) - 1]);
        if ($code === 0xd9) { hash_update($context, $marker); return hash_final($context); }
        if ($code === 0x01 || ($code >= 0xd0 && $code <= 0xd8)) { hash_update($context, $marker); continue; }
        $lengthBytes = $readExact(2); $length = unpack('n', $lengthBytes)[1];
        if ($length < 2) throw new InvalidArgumentException('invalid JPEG segment length');
        $retained = !in_array($code, [0xe1, 0xed, 0xfe], true);
        if ($retained) { hash_update($context, $marker); hash_update($context, $lengthBytes); }
        $remaining = $length - 2;
        while ($remaining > 0) {
            $part = $readExact(min($remaining, 65536));
            if ($retained) hash_update($context, $part);
            $remaining -= strlen($part);
        }
        $inScan = $code === 0xda;
    }
}

function jpeg_content_sha256(string $path): string
{
    $stream = fopen($path, 'rb');
    if ($stream === false) throw new RuntimeException("unable to read $path");
    try { return jpeg_content_sha256_stream($stream); } finally { fclose($stream); }
}
