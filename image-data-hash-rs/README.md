# image-data-hash for Rust

Native JPEG ImageDataHash. Cargo package: `image-data-hash`.
Rust import: `image_data_hash`. Requires an edition-2024-capable Rust toolchain.

## Installation

```toml
[dependencies]
image-data-hash = "0.1"
```

For local development, a Cargo path dependency can point to this directory.

## Usage

```rust
use image_data_hash::{
    Algorithm, image_data_hash, image_data_hash_with_algorithm,
    image_data_hash_bytes, image_data_hash_reader,
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let md5 = image_data_hash("photo.jpg")?;
    let sha256 = image_data_hash_with_algorithm("photo.jpg", Algorithm::Sha256)?;
    let sha512 = image_data_hash_with_algorithm("photo.jpg", Algorithm::Sha512)?;

    let file = std::fs::File::open("photo.jpg")?;
    let streamed = image_data_hash_reader(file, Algorithm::default())?;
    let bytes = std::fs::read("photo.jpg")?;
    let buffered = image_data_hash_bytes(&bytes, Algorithm::Sha256)?;
    Ok(())
}
```

`Algorithm::default()` is MD5. Reader and bytes APIs require an explicit enum
argument because Rust does not have default function arguments. Results are
lowercase hexadecimal strings wrapped in `anyhow::Result`. Readers are buffered
internally; pass `&mut reader` to retain ownership, noting possible read-ahead.
Runtime dependencies are `anyhow`, `md-5` and `sha2`.

## Tests

Generate the [shared fixtures](https://github.com/bencevans/image-data-hash/blob/main/fixtures/README.md), then:

```sh
cd image-data-hash-rs
cargo fmt --check
cargo test --locked
cargo doc --no-deps
```

See [compatibility rules](https://github.com/bencevans/image-data-hash/blob/main/SPEC.md).

## Project

Repository: [bencevans/image-data-hash](https://github.com/bencevans/image-data-hash). Maintainer: Ben Evans. Licensed under MIT.
