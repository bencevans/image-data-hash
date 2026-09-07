import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  imageDataHash,
  imageDataHashBytes,
  imageDataHashStream,
} from "./dist/index.js";

const directory =
  process.env.JPEG_HASH_FIXTURES ||
  fileURLToPath(new URL("../fixtures/generated", import.meta.url));
const manifest = await readFile(resolve(directory, "manifest.tsv"), "utf8");
const rows = manifest
  .trim()
  .split("\n")
  .slice(1)
  .map((line) => line.split("\t"));
assert.equal(
  rows.length,
  41,
  "Generate all compatibility fixtures before testing",
);

for (const [name, ...hashes] of rows) {
  test(name + " matches ExifTool for all algorithms", async () => {
    const path = resolve(directory, name);
    const data = await readFile(path);
    for (const [index, algorithm] of ["md5", "sha256", "sha512"].entries()) {
      assert.equal(await imageDataHash(path, algorithm), hashes[index]);
      assert.equal(imageDataHashBytes(data, algorithm), hashes[index]);
    }
  });
}

test("default, aliases and rejected algorithms", async () => {
  const [name, md5, sha256, sha512] = rows[0];
  const data = await readFile(resolve(directory, name));
  assert.equal(imageDataHashBytes(data), md5);
  assert.equal(imageDataHashBytes(data, "SHA-256"), sha256);
  assert.equal(imageDataHashBytes(data, "SHA-512"), sha512);
  assert.throws(() => imageDataHashBytes(data, "sha1"));
});

test("one-byte asynchronous chunks and iterator cleanup", async () => {
  for (const [name, expected] of rows.filter((row) =>
    row[0].startsWith("structural"),
  )) {
    const data = await readFile(resolve(directory, name));
    let closed = false;
    async function* chunks() {
      try {
        for (const byte of data) yield Buffer.from([byte]);
      } finally {
        closed = true;
      }
    }
    assert.equal(await imageDataHashStream(chunks()), expected);
    assert.equal(closed, true);
  }
});

test("rejects invalid input", () => {
  for (const hex of [
    "",
    "00010203",
    "ffd8",
    "ffd8ffe100",
    "ffd8ffe10001",
    "ffd8ffd9",
    "ffd8ffda000261ff",
  ]) {
    assert.throws(() => imageDataHashBytes(Buffer.from(hex, "hex")), hex);
  }
});
