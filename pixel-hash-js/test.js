import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { Readable } from "node:stream";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { jpegContentSha256, jpegContentSha256Bytes, jpegContentSha256Stream } from "./index.js";

const vectors = new Map([
  [new URL("../fixtures/IMG_0787.JPG", import.meta.url), "fdc79d5549c0fa9190c422afc9ae506964904a328ff5c67ef6298cd5ead8e6b7"],
  [new URL("../fixtures/IMG_1039.JPG", import.meta.url), "8cb0c2dfb0fb6a2bb7ecd28555dd49ada047b2bb45c53be4aeea7d56edc86b9d"],
]);

test("shared generated EXIF variants match fixed hashes", async () => {
  const directory = process.env.JPEG_HASH_FIXTURES || fileURLToPath(new URL("../fixtures/generated", import.meta.url));
  const rows = (await readFile(resolve(directory, "manifest.tsv"), "utf8")).trim().split("\n").slice(1);
  assert.equal(rows.length, 30);
  for (const row of rows) {
    const [name, expected] = row.split("\t");
    const path = resolve(directory, name);
    assert.equal(await jpegContentSha256(path), expected, name);
    assert.equal(jpegContentSha256Bytes(await readFile(path)), expected, name);
  }
});
const segment = (marker, payload) => {
  const body = Buffer.from(payload);
  const result = Buffer.alloc(body.length + 4);
  result[0] = 0xff; result[1] = marker; result.writeUInt16BE(body.length + 2, 2); body.copy(result, 4);
  return result;
};

test("known cross-language hashes", async () => {
  for (const [fixture, expected] of vectors) assert.equal(await jpegContentSha256(fixture), expected);
});
test("ignores metadata but retains ICC", async () => {
  for (const [fixture, hash] of vectors) {
    const original = await readFile(fixture);
    for (const marker of [0xe1, 0xed, 0xfe]) {
      assert.equal(jpegContentSha256Bytes(Buffer.concat([original.subarray(0, 2), segment(marker, "metadata"), original.subarray(2)])), hash);
    }
    assert.equal(jpegContentSha256Bytes(Buffer.concat([original, Buffer.from("vendor trailer")])), hash);
  }
  const [fixture, hash] = vectors.entries().next().value;
  const original = await readFile(fixture);
  assert.notEqual(jpegContentSha256Bytes(Buffer.concat([original.subarray(0, 2), segment(0xe2, "ICC"), original.subarray(2)])), hash);
});
test("rejects malformed input", () => assert.throws(() => jpegContentSha256Bytes(Buffer.from("not jpeg"))));
test("streaming supports tiny chunks", async () => {
  const [fixture, expected] = vectors.entries().next().value;
  const data = await readFile(fixture);
  const chunks = []; for (let i = 0; i < data.length; i += 7) chunks.push(data.subarray(i, i + 7));
  assert.equal(await jpegContentSha256Stream(Readable.from(chunks)), expected);
});
