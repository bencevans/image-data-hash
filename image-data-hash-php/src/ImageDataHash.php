<?php

declare(strict_types=1);

namespace ImageDataHash;

/** @internal Normalize the three algorithms supported by ExifTool. */
function normalize_algorithm(string $algorithm): string
{
    $algorithm = str_replace('-', '', strtolower($algorithm));
    if (!in_array($algorithm, ['md5', 'sha256', 'sha512'], true)) {
        throw new \InvalidArgumentException('Unsupported hash algorithm');
    }
    return $algorithm;
}

/**
 * Hash JPEG data from an open blocking binary stream.
 *
 * The caller retains ownership of the stream. Reading stops at EOI, but PHP's
 * stream buffering may read ahead. Metadata and tables before scans are skipped.
 *
 * @param resource $stream Readable binary stream positioned at the JPEG signature.
 * @param string $algorithm MD5 (default), SHA-256 or SHA-512; case-insensitive.
 * @return string Lowercase hexadecimal digest: 32, 64 or 128 characters.
 * @throws \InvalidArgumentException On invalid input, failed reads or unsupported algorithms.
 */
function image_data_hash_stream($stream, string $algorithm = 'md5'): string
{
    if (!is_resource($stream)) {
        throw new \InvalidArgumentException('Expected a readable stream');
    }
    $digest = hash_init(normalize_algorithm($algorithm));
    $readExact = function (int $length) use ($stream): string {
        $result = '';
        while (strlen($result) < $length) {
            $part = fread($stream, $length - strlen($result));
            if ($part === false || $part === '') {
                throw new \InvalidArgumentException('Truncated JPEG or missing EOI');
            }
            $result .= $part;
        }
        return $result;
    };
    if ($readExact(2) !== "\xff\xd8") {
        throw new \InvalidArgumentException('Not a JPEG file');
    }

    $candidate = null;
    $foundScan = false;
    while (true) {
        // Hold a tentative digest for the current scan chunk. ExifTool only
        // includes it if the following marker has no length field.
        $buffer = '';
        while (($byte = $readExact(1)) !== "\xff") {
            $buffer .= $byte;
            if (strlen($buffer) >= 65536) {
                if ($candidate !== null) {
                    hash_update($candidate, $buffer);
                }
                $buffer = '';
            }
        }
        if ($candidate !== null) {
            hash_update($candidate, $buffer);
        }

        $fillCount = 0;
        while (($byte = $readExact(1)) === "\xff") {
            ++$fillCount;
        }
        $code = ord($byte);
        $standalone = $code === 0 || $code === 1 || ($code >= 0xd0 && $code <= 0xda);
        if ($candidate !== null && $standalone) {
            while ($fillCount > 0) {
                $count = min($fillCount, 65536);
                hash_update($candidate, str_repeat("\xff", $count));
                $fillCount -= $count;
            }
            $digest = $candidate;
        }
        $candidate = null;

        if ($code === 0xd9) {
            if (!$foundScan) {
                throw new \InvalidArgumentException('JPEG has no SOS');
            }
            return hash_final($digest);
        }
        if ($code === 0xda) {
            $foundScan = true;
        }
        if ($code === 0 || $code === 0xda || ($code >= 0xd0 && $code <= 0xd7)) {
            $candidate = hash_copy($digest);
            hash_update($candidate, "\xff" . chr($code));
        }

        if (!$standalone) {
            $length = unpack('n', $readExact(2))[1];
            if ($length < 2) {
                throw new \InvalidArgumentException('Invalid JPEG segment length');
            }
            $readExact($length - 2);
        }
    }
}

/**
 * Hash an in-memory JPEG. Bytes after EOI are ignored.
 *
 * This helper copies the data into a PHP memory stream. For large files, use
 * image_data_hash() or image_data_hash_stream() to avoid that copy.
 *
 * @param string $data Binary JPEG bytes, not a base64 string.
 * @param string $algorithm MD5 (default), SHA-256 or SHA-512; case-insensitive.
 * @return string Lowercase hexadecimal digest.
 * @throws \InvalidArgumentException On malformed data or unsupported algorithms.
 */
function image_data_hash_bytes(string $data, string $algorithm = 'md5'): string
{
    $stream = fopen('php://memory', 'w+b');
    try {
        fwrite($stream, $data);
        rewind($stream);
        return image_data_hash_stream($stream, $algorithm);
    } finally {
        fclose($stream);
    }
}

/**
 * Hash a JPEG file and close its stream on completion or error.
 *
 * @param string $path Path to a readable JPEG file.
 * @param string $algorithm MD5 (default), SHA-256 or SHA-512; case-insensitive.
 * @return string Lowercase hexadecimal digest.
 * @throws \RuntimeException When the file cannot be opened.
 * @throws \InvalidArgumentException On malformed data, failed reads or unsupported algorithms.
 */
function image_data_hash(string $path, string $algorithm = 'md5'): string
{
    $stream = fopen($path, 'rb');
    if ($stream === false) {
        throw new \RuntimeException("Unable to read $path");
    }
    try {
        return image_data_hash_stream($stream, $algorithm);
    } finally {
        fclose($stream);
    }
}
