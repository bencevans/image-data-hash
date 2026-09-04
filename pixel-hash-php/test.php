<?php
require __DIR__ . '/src/JpegContentHash.php';
$directory = getenv('JPEG_HASH_FIXTURES') ?: __DIR__ . '/../fixtures/generated';
$manifest = fopen($directory . '/manifest.tsv', 'rb');
if ($manifest === false) throw new RuntimeException('Run fixtures/generate.py first');
fgetcsv($manifest, 0, "\t", '"', '');
$count = 0;
while (($row = fgetcsv($manifest, 0, "\t", '"', '')) !== false) {
    [$name, $expected] = $row;
    $path = $directory . '/' . $name;
    if (jpeg_content_sha256($path) !== $expected || jpeg_content_sha256_bytes(file_get_contents($path)) !== $expected) {
        throw new RuntimeException("Hash mismatch: $name");
    }
    ++$count;
}
fclose($manifest);
if ($count !== 30) throw new RuntimeException('Expected 30 generated variants');
$vectors = [
    'IMG_0787.JPG' => 'fdc79d5549c0fa9190c422afc9ae506964904a328ff5c67ef6298cd5ead8e6b7',
    'IMG_1039.JPG' => '8cb0c2dfb0fb6a2bb7ecd28555dd49ada047b2bb45c53be4aeea7d56edc86b9d',
];
$segment = fn(int $marker, string $body): string => "\xff" . chr($marker) . pack('n', strlen($body) + 2) . $body;
foreach ($vectors as $name => $expected) {
    $fixture = __DIR__ . '/../fixtures/' . $name; $data = file_get_contents($fixture);
    assert(jpeg_content_sha256($fixture) === $expected);
    $stream = fopen($fixture, 'rb'); assert(jpeg_content_sha256_stream($stream) === $expected); fclose($stream);
    $insert = fn(int $marker): string => substr($data, 0, 2) . $segment($marker, 'metadata') . substr($data, 2);
    foreach ([0xe1, 0xed, 0xfe] as $marker) assert(jpeg_content_sha256_bytes($insert($marker)) === $expected);
    assert(jpeg_content_sha256_bytes($data . 'vendor trailer') === $expected);
}
assert(jpeg_content_sha256_bytes($insert(0xe2)) !== $expected);
try { jpeg_content_sha256_bytes('not jpeg'); assert(false); } catch (InvalidArgumentException $e) {}
echo "PHP tests passed\n";
