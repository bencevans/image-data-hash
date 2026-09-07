<?php

require __DIR__ . '/src/ImageDataHash.php';

use function ImageDataHash\image_data_hash;
use function ImageDataHash\image_data_hash_bytes;
use function ImageDataHash\image_data_hash_stream;

function check_equal(string $actual, string $expected, string $case): void
{
    if ($actual !== $expected) {
        throw new RuntimeException("Hash mismatch: $case");
    }
}

$directory = getenv('JPEG_HASH_FIXTURES') ?: __DIR__ . '/../fixtures/generated';
$manifest = fopen($directory . '/manifest.tsv', 'rb');
if ($manifest === false) {
    throw new RuntimeException('Generate the compatibility fixtures first');
}
fgetcsv($manifest, 0, "\t", '"', '');
$count = 0;
while (($row = fgetcsv($manifest, 0, "\t", '"', '')) !== false) {
    [$name, $md5, $sha256, $sha512] = $row;
    $path = $directory . '/' . $name;
    $data = file_get_contents($path);
    check_equal(image_data_hash($path), $md5, $name);
    foreach (['md5' => $md5, 'sha256' => $sha256, 'sha512' => $sha512] as $algorithm => $expected) {
        check_equal(image_data_hash($path, $algorithm), $expected, $name);
        check_equal(image_data_hash_bytes($data, $algorithm), $expected, $name);
        $stream = fopen($path, 'rb');
        check_equal(image_data_hash_stream($stream, $algorithm), $expected, $name);
        fclose($stream);
    }
    ++$count;
}
fclose($manifest);
if ($count !== 41) {
    throw new RuntimeException('Expected 41 compatibility fixtures');
}
check_equal(image_data_hash_bytes($data, 'SHA-256'), $sha256, 'alias');
check_equal(image_data_hash_bytes($data, 'SHA-512'), $sha512, 'alias');
foreach (['', '00010203', 'ffd8', 'ffd8ffe100', 'ffd8ffe10001', 'ffd8ffd9', 'ffd8ffda000261ff'] as $hex) {
    try {
        image_data_hash_bytes(hex2bin($hex));
    } catch (InvalidArgumentException $error) {
        continue;
    }
    throw new RuntimeException("Accepted invalid JPEG: $hex");
}
try {
    image_data_hash_bytes($data, 'sha1');
    throw new RuntimeException('Accepted unsupported algorithm');
} catch (InvalidArgumentException $error) {
    // Expected.
}
echo "All PHP compatibility tests passed\n";
