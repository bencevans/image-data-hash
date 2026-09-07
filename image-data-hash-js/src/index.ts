import { createHash, type Hash } from "node:crypto";
import { createReadStream, type PathLike } from "node:fs";

/** Supported algorithms. Names are case-insensitive and may include hyphens. */
export type Algorithm =
  | "md5"
  | "MD5"
  | "sha256"
  | "SHA256"
  | "sha-256"
  | "SHA-256"
  | "sha512"
  | "SHA512"
  | "sha-512"
  | "SHA-512";

const MARKER_PREFIX = 0xff;
const START_OF_IMAGE = 0xd8;
const START_OF_SCAN = 0xda;
const END_OF_IMAGE = 0xd9;
const BUFFER_SIZE = 65536;

enum ParseState {
  Signature,
  ScanData,
  MarkerCode,
  LengthHighByte,
  LengthLowByte,
  SegmentPayload,
}

/** ExifTool treats SOS as lengthless so its header joins the scan data. */
function hasLengthField(marker: number): boolean {
  return !(marker === 0 || marker === 1 || (marker >= 0xd0 && marker <= 0xda));
}

/** SOS, escaped FF bytes and restart markers can begin a hashed chunk. */
function startsHashChunk(marker: number): boolean {
  return (
    marker === 0 ||
    marker === START_OF_SCAN ||
    (marker >= 0xd0 && marker <= 0xd7)
  );
}

function normalizeAlgorithm(algorithm: string): string {
  const normalized = algorithm.toLowerCase().replaceAll("-", "");
  if (!["md5", "sha256", "sha512"].includes(normalized)) {
    throw new RangeError("algorithm must be MD5, SHA-256 or SHA-512");
  }
  return normalized;
}

/**
 * Incremental JPEG parser shared by the stream and buffer APIs.
 *
 * ExifTool includes a scan chunk only if the following marker has no length
 * field. A tentative hash lets us commit or discard that chunk without storing it.
 */
class JpegHasher {
  private digest: Hash;
  private pendingDigest: Hash | null = null;
  private state = ParseState.Signature;
  private signature: number[] = [];
  private fillByteCount = 0;
  private payloadBytesRemaining = 0;
  private lengthHighByte = 0;
  private foundScan = false;
  private result: string | null = null;

  constructor(algorithm: Algorithm) {
    this.digest = createHash(normalizeAlgorithm(algorithm));
  }

  get complete(): boolean {
    return this.result !== null;
  }

  /** Feed another binary chunk; markers may span arbitrary chunk boundaries. */
  update(input: Uint8Array): void {
    if (!(input instanceof Uint8Array)) {
      throw new TypeError("Expected a Uint8Array or Buffer");
    }
    const chunk = Buffer.from(input.buffer, input.byteOffset, input.byteLength);
    let position = 0;

    while (position < chunk.length && !this.complete) {
      switch (this.state) {
        case ParseState.Signature:
          this.readSignatureByte(chunk[position++]);
          break;

        case ParseState.SegmentPayload: {
          const count = Math.min(
            this.payloadBytesRemaining,
            chunk.length - position,
          );
          position += count;
          this.payloadBytesRemaining -= count;
          if (this.payloadBytesRemaining === 0) {
            this.state = ParseState.ScanData;
          }
          break;
        }

        case ParseState.LengthHighByte:
          this.lengthHighByte = chunk[position++];
          this.state = ParseState.LengthLowByte;
          break;

        case ParseState.LengthLowByte:
          this.readLengthLowByte(chunk[position++]);
          break;

        case ParseState.ScanData:
          position = this.readScanData(chunk, position);
          break;

        case ParseState.MarkerCode:
          this.readMarkerByte(chunk[position++]);
          break;
      }
    }
  }

  private readSignatureByte(byte: number): void {
    this.signature.push(byte);
    if (this.signature.length < 2) {
      return;
    }
    if (
      this.signature[0] !== MARKER_PREFIX ||
      this.signature[1] !== START_OF_IMAGE
    ) {
      throw new Error("Not a JPEG file");
    }
    this.state = ParseState.ScanData;
  }

  /** Segment length includes the two length bytes themselves. */
  private readLengthLowByte(byte: number): void {
    const segmentLength = this.lengthHighByte * 256 + byte;
    if (segmentLength < 2) {
      throw new Error("Invalid JPEG segment length");
    }
    this.payloadBytesRemaining = segmentLength - 2;
    this.state =
      this.payloadBytesRemaining > 0
        ? ParseState.SegmentPayload
        : ParseState.ScanData;
  }

  /** Hash ordinary bytes in bulk, stopping at the next FF marker prefix. */
  private readScanData(chunk: Buffer, position: number): number {
    const markerPosition = chunk.indexOf(MARKER_PREFIX, position);
    const end = markerPosition < 0 ? chunk.length : markerPosition;
    this.pendingDigest?.update(chunk.subarray(position, end));

    if (markerPosition < 0) {
      return end;
    }
    this.fillByteCount = 0;
    this.state = ParseState.MarkerCode;
    return end + 1;
  }

  private readMarkerByte(marker: number): void {
    if (marker === MARKER_PREFIX) {
      this.fillByteCount++;
      return;
    }

    if (!hasLengthField(marker) && this.pendingDigest !== null) {
      // Preserve extra FF fill bytes, but exclude the final marker prefix.
      while (this.fillByteCount > 0) {
        const count = Math.min(this.fillByteCount, BUFFER_SIZE);
        this.pendingDigest.update(Buffer.alloc(count, MARKER_PREFIX));
        this.fillByteCount -= count;
      }
      this.digest = this.pendingDigest;
    }
    this.pendingDigest = null;

    if (marker === END_OF_IMAGE) {
      if (!this.foundScan) {
        throw new Error("JPEG has no start-of-scan marker");
      }
      this.result = this.digest.digest("hex");
      return;
    }
    if (marker === START_OF_SCAN) {
      this.foundScan = true;
    }
    if (startsHashChunk(marker)) {
      this.pendingDigest = this.digest.copy();
      this.pendingDigest.update(Buffer.from([MARKER_PREFIX, marker]));
    }
    this.state = hasLengthField(marker)
      ? ParseState.LengthHighByte
      : ParseState.ScanData;
  }

  finish(): string {
    if (this.result === null) {
      throw new Error("Truncated JPEG or missing end-of-image marker");
    }
    return this.result;
  }
}

/**
 * Hash JPEG bytes without an external process.
 * @param data Complete JPEG bytes; trailing data after EOI is ignored.
 * @param algorithm MD5 by default; SHA-256 and SHA-512 are also supported.
 * @returns Lowercase hexadecimal digest (32, 64 or 128 characters).
 * @throws If the input is malformed or the algorithm is unsupported.
 */
export function imageDataHashBytes(
  data: Uint8Array,
  algorithm: Algorithm = "md5",
): string {
  const hasher = new JpegHasher(algorithm);
  hasher.update(data);
  return hasher.finish();
}

/**
 * Hash binary chunks from a Node.js readable or an async iterable.
 * Stops at EOI and closes the iterator. Input may be consumed ahead of EOI.
 * @param source Async iterable of Uint8Array/Buffer chunks.
 * @param algorithm MD5 by default.
 * @returns A lowercase hexadecimal digest.
 * @throws If reading fails, the JPEG is malformed, or the algorithm is unsupported.
 */
export async function imageDataHashStream(
  source: AsyncIterable<Uint8Array>,
  algorithm: Algorithm = "md5",
): Promise<string> {
  const hasher = new JpegHasher(algorithm);
  for await (const chunk of source) {
    hasher.update(chunk);
    if (hasher.complete) {
      break;
    }
  }
  return hasher.finish();
}

/**
 * Hash a JPEG file using bounded working memory.
 * @param path File path, Buffer path, or file URL accepted by Node.js.
 * @param algorithm MD5 by default.
 * @returns A lowercase hexadecimal digest.
 * @throws If the file cannot be read, its JPEG data is malformed, or the algorithm is unsupported.
 */
export async function imageDataHash(
  path: PathLike,
  algorithm: Algorithm = "md5",
): Promise<string> {
  const stream = createReadStream(path);
  try {
    return await imageDataHashStream(stream, algorithm);
  } finally {
    stream.destroy();
  }
}
