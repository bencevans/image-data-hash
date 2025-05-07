# Pixel Hash

> [!WARNING]
> This is not yet complete and requires some additional work to ensure uniformity between languages.

The aim of the contained Pixel Hash libraries is to provide a simple way to identify images based on the their raw pixel data (ignoring any metadata or EXIF differences).

The reason for developing these libraries is with Camera Trap imagery in mind, where images are often annotated with species information in the EXIF metadata and we need to identify duplicate images stored across filesystems.

There's currently three implementations:

- [Python](./pixel-hash-python/)
- [R](./pixel-hash-r/)
- [Rust](./pixel-hash-rust/)
