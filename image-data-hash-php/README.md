# image-data-hash for PHP

Native JPEG ImageDataHash for PHP 8.0+ with the standard hash extension.
Composer name: `bencevans/image-data-hash`. PHP namespace: `ImageDataHash`.


## Installation

```sh
composer require bencevans/image-data-hash
```

Composer's autoloader includes the exported functions. For local development, configure a Composer path repository pointing to this directory.

```php
require 'vendor/autoload.php';

use function ImageDataHash\image_data_hash;
use function ImageDataHash\image_data_hash_bytes;
use function ImageDataHash\image_data_hash_stream;

$md5 = image_data_hash('photo.jpg');
$sha256 = image_data_hash('photo.jpg', 'sha256');
$sha512 = image_data_hash('photo.jpg', 'sha512');

$stream = fopen('photo.jpg', 'rb');
try {
    $digest = image_data_hash_stream($stream, 'sha256');
} finally {
    fclose($stream);
}
$digest = image_data_hash_bytes($jpegBytes, 'sha256');
```

MD5 is the default. Names are case-insensitive and accept hyphens.
Returns lowercase hexadecimal strings. Stream hashing uses bounded working
memory and leaves caller-owned blocking streams open. The bytes helper copies
the input into an in-memory PHP stream.

Malformed JPEGs or unsupported algorithms raise `InvalidArgumentException`;
file failures raise `RuntimeException` (PHP may also emit an I/O warning).
Only JPEG is supported. See [compatibility rules](https://github.com/bencevans/image-data-hash/blob/main/SPEC.md).

## Tests

Generate the [shared fixtures](https://github.com/bencevans/image-data-hash/blob/main/fixtures/README.md), then:

```sh
cd image-data-hash-php
composer install
composer format:check
composer test
```

Tests use explicit exceptions, so PHP assertion settings do not affect coverage.

## Project

Repository: [bencevans/image-data-hash](https://github.com/bencevans/image-data-hash). Maintainer: Ben Evans. Licensed under MIT.
