import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";

const IGNORED = new Set([0xe1, 0xed, 0xfe]);

function canonicalChunks(input) {
  const data = Buffer.from(input);
  if (data.length < 4 || data[0] !== 0xff || data[1] !== 0xd8) throw new Error("not a JPEG file");
  const chunks = [data.subarray(0, 2)];
  let pos = 2, inScan = false, scanStart = 0;
  while (pos < data.length) {
    const markerStart = pos;
    if (data[pos] !== 0xff) {
      if (!inScan) throw new Error(`unexpected data at offset ${pos}`);
      pos++;
      continue;
    }
    while (pos < data.length && data[pos] === 0xff) pos++;
    if (pos === data.length) throw new Error("truncated JPEG marker");
    const marker = data[pos++];
    if (inScan && marker === 0x00) continue;
    if (inScan && marker >= 0xd0 && marker <= 0xd7) continue;
    if (inScan) {
      chunks.push(data.subarray(scanStart, markerStart));
      inScan = false;
    }
    if (marker === 0xd9) {
      chunks.push(data.subarray(markerStart, pos));
      return chunks;
    }
    if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd8)) {
      chunks.push(data.subarray(markerStart, pos));
      continue;
    }
    if (pos + 2 > data.length) throw new Error("truncated JPEG segment length");
    const length = data.readUInt16BE(pos);
    if (length < 2 || pos + length > data.length) throw new Error("invalid or truncated JPEG segment");
    const end = pos + length;
    if (!IGNORED.has(marker)) chunks.push(data.subarray(markerStart, end));
    pos = end;
    inScan = marker === 0xda;
    if (inScan) scanStart = pos;
  }
  throw new Error("JPEG has no EOI marker");
}

export function canonicalJpeg(input) {
  return Buffer.concat(canonicalChunks(input));
}

export function jpegContentSha256Bytes(data) {
  const digest = createHash("sha256");
  for (const chunk of canonicalChunks(data)) digest.update(chunk);
  return digest.digest("hex");
}

export async function jpegContentSha256Stream(source) {
  const digest = createHash("sha256");
  let state = "soi", soi = [], marker = [], lengthHigh = 0;
  let remaining = 0, retained = false, afterPayload = "markerPrefix", finished = false;

  const handleMarker = code => {
    const bytes = Buffer.from(marker);
    if (code === 0xd9) { digest.update(bytes); finished = true; return; }
    if (code === 0x01 || (code >= 0xd0 && code <= 0xd8)) {
      digest.update(bytes); state = "markerPrefix"; return;
    }
    retained = !IGNORED.has(code);
    state = "lengthHigh";
  };

  for await (const value of source) {
    const chunk = Buffer.from(value);
    let pos = 0;
    while (pos < chunk.length && !finished) {
      if (state === "soi") {
        soi.push(chunk[pos++]);
        if (soi.length === 2) {
          if (soi[0] !== 0xff || soi[1] !== 0xd8) throw new Error("not a JPEG file");
          digest.update(Buffer.from(soi)); state = "markerPrefix";
        }
      } else if (state === "markerPrefix") {
        if (chunk[pos++] !== 0xff) throw new Error("unexpected data outside JPEG scan");
        marker = [0xff]; state = "markerCode";
      } else if (state === "markerCode") {
        const code = chunk[pos++]; marker.push(code);
        if (code !== 0xff) handleMarker(code);
      } else if (state === "lengthHigh") {
        lengthHigh = chunk[pos++]; state = "lengthLow";
      } else if (state === "lengthLow") {
        const low = chunk[pos++]; const length = lengthHigh * 256 + low;
        if (length < 2) throw new Error("invalid JPEG segment length");
        if (retained) { digest.update(Buffer.from(marker)); digest.update(Buffer.from([lengthHigh, low])); }
        remaining = length - 2;
        afterPayload = marker[marker.length - 1] === 0xda ? "scan" : "markerPrefix";
        state = remaining ? "payload" : afterPayload;
      } else if (state === "payload") {
        const count = Math.min(remaining, chunk.length - pos);
        if (retained) digest.update(chunk.subarray(pos, pos + count));
        pos += count; remaining -= count;
        if (!remaining) state = afterPayload;
      } else if (state === "scan") {
        const nextMarker = chunk.indexOf(0xff, pos);
        if (nextMarker < 0) { digest.update(chunk.subarray(pos)); pos = chunk.length; }
        else {
          if (nextMarker > pos) digest.update(chunk.subarray(pos, nextMarker));
          pos = nextMarker + 1; marker = [0xff]; state = "scanMarker";
        }
      } else if (state === "scanMarker") {
        const code = chunk[pos++]; marker.push(code);
        if (code === 0xff) continue;
        if (code === 0 || (code >= 0xd0 && code <= 0xd7)) { digest.update(Buffer.from(marker)); state = "scan"; }
        else handleMarker(code);
      }
    }
    if (finished) return digest.digest("hex");
  }
  throw new Error(state.includes("marker") ? "truncated JPEG marker" : "JPEG has no EOI marker");
}

export function jpegContentSha256(path) {
  return jpegContentSha256Stream(createReadStream(path));
}
