import {
  imageDataHash,
  imageDataHashBytes,
  imageDataHashStream,
  type Algorithm,
} from "./dist/index.js";

const algorithm: Algorithm = "SHA-512";
const pathResult: Promise<string> = imageDataHash("photo.jpg", algorithm);
const byteResult: string = imageDataHashBytes(new Uint8Array(), "md5");
const streamResult: Promise<string> = imageDataHashStream(
  (async function* () {
    yield new Uint8Array();
  })(),
  "sha256",
);

// These are compile-time checks only; this file is never executed.
void [pathResult, byteResult, streamResult];
// @ts-expect-error Unsupported algorithms must be rejected by the declarations.
imageDataHashBytes(new Uint8Array(), "sha1");
// @ts-expect-error Text is not binary JPEG input.
imageDataHashBytes("not bytes");
