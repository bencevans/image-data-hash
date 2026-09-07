# image-data-hash for TypeScript and JavaScript

Native JPEG ImageDataHash for Node.js 18+. Package name: `image-data-hash`.
ES modules with bundled TypeScript declarations; no external runtime dependencies.

## Installation

```sh
npm install image-data-hash
```

The package ships compiled JavaScript, source maps, and declaration files. Both JavaScript and TypeScript consumers use the same imports. The exported `Algorithm` type lists accepted names; the compiler catches unsupported choices.

## Usage

```js
import { createReadStream } from "node:fs";
import {
  imageDataHash,
  imageDataHashBytes,
  imageDataHashStream,
} from "image-data-hash";

const md5 = await imageDataHash("photo.jpg");
const sha256 = await imageDataHash("photo.jpg", "sha256");
const sha512 = await imageDataHash("photo.jpg", "sha512");
const streamed = await imageDataHashStream(
  createReadStream("photo.jpg"),
  "sha256",
);
const buffered = imageDataHashBytes(jpegBuffer, "sha256");
```

MD5 is the default. Algorithm names are case-insensitive and accept hyphens.
Results are lowercase hexadecimal strings. Buffers must be `Uint8Array` or
`Buffer`; streams must be async iterables of binary chunks. The synchronous bytes
API and asynchronous stream API use the same parser. Working memory is bounded
by input chunk size. Stream iteration ends at EOI and closes the iterator.

Malformed input and unsupported algorithms throw (or reject the returned promise).
Only JPEG is supported. See [compatibility rules](https://github.com/bencevans/image-data-hash/blob/main/SPEC.md).

## Tests

Generate the [shared fixtures](https://github.com/bencevans/image-data-hash/blob/main/fixtures/README.md), then:

```sh
cd image-data-hash-js
npm ci
npm test
npm run format:check
```

## Project

Repository: [bencevans/image-data-hash](https://github.com/bencevans/image-data-hash). Maintainer: Ben Evans. Licensed under MIT.
