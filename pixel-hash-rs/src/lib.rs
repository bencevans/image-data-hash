//! Streaming `jpeg_content_sha256_v1` implementation.

use anyhow::{Result, bail};
use sha2::{Digest, Sha256};
use std::fs::File;
use std::io::{BufReader, Cursor, Read};
use std::path::Path;

fn byte<R: Read>(source: &mut R, message: &str) -> Result<u8> {
    let mut value = [0u8; 1];
    if source.read(&mut value)? == 0 {
        bail!(message.to_owned());
    }
    Ok(value[0])
}

pub fn jpeg_content_sha256_reader<R: Read>(mut source: R) -> Result<String> {
    let mut digest = Sha256::new();
    let mut soi = [0u8; 2];
    source.read_exact(&mut soi)?;
    if soi != [0xff, 0xd8] {
        bail!("not a JPEG file");
    }
    digest.update(soi);
    let mut in_scan = false;
    let mut pending: Option<Vec<u8>> = None;
    let mut scan = Vec::with_capacity(65536);

    loop {
        if in_scan && pending.is_none() {
            let value = byte(&mut source, "JPEG has no EOI marker")?;
            if value != 0xff {
                scan.push(value);
                if scan.len() == scan.capacity() {
                    digest.update(&scan);
                    scan.clear();
                }
                continue;
            }
            let mut marker = vec![value];
            let code = loop {
                let value = byte(&mut source, "truncated JPEG marker")?;
                marker.push(value);
                if value != 0xff {
                    break value;
                }
            };
            if code == 0 || (0xd0..=0xd7).contains(&code) {
                scan.extend_from_slice(&marker);
                continue;
            }
            digest.update(&scan);
            scan.clear();
            in_scan = false;
            pending = Some(marker);
        }

        let marker = if let Some(marker) = pending.take() {
            marker
        } else {
            if byte(&mut source, "JPEG has no EOI marker")? != 0xff {
                bail!("unexpected data outside JPEG scan");
            }
            let mut marker = vec![0xff];
            loop {
                let value = byte(&mut source, "truncated JPEG marker")?;
                marker.push(value);
                if value != 0xff {
                    break;
                }
            }
            marker
        };
        let code = *marker.last().unwrap();
        if code == 0xd9 {
            digest.update(&marker);
            return Ok(format!("{:x}", digest.finalize()));
        }
        if code == 0x01 || (0xd0..=0xd8).contains(&code) {
            digest.update(&marker);
            continue;
        }

        let mut length_bytes = [0u8; 2];
        source.read_exact(&mut length_bytes)?;
        let length = u16::from_be_bytes(length_bytes) as usize;
        if length < 2 {
            bail!("invalid JPEG segment length");
        }
        let retained = !matches!(code, 0xe1 | 0xed | 0xfe);
        if retained {
            digest.update(&marker);
            digest.update(length_bytes);
        }
        let mut remaining = length - 2;
        let mut buffer = [0u8; 65536];
        while remaining != 0 {
            let count = remaining.min(buffer.len());
            source.read_exact(&mut buffer[..count])?;
            if retained {
                digest.update(&buffer[..count]);
            }
            remaining -= count;
        }
        in_scan = code == 0xda;
    }
}

pub fn jpeg_content_sha256_bytes(data: &[u8]) -> Result<String> {
    jpeg_content_sha256_reader(Cursor::new(data))
}

pub fn jpeg_content_sha256<P: AsRef<Path>>(path: P) -> Result<String> {
    jpeg_content_sha256_reader(BufReader::new(File::open(path)?))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn shared_generated_exif_variants() {
        let directory =
            std::env::var("JPEG_HASH_FIXTURES").unwrap_or_else(|_| "../fixtures/generated".into());
        let manifest = std::fs::read_to_string(Path::new(&directory).join("manifest.tsv"))
            .expect("Run fixtures/generate.py first");
        let rows: Vec<_> = manifest.lines().skip(1).collect();
        assert_eq!(rows.len(), 30);
        for row in rows {
            let (name, expected) = row.split_once('\t').unwrap();
            let path = Path::new(&directory).join(name);
            assert_eq!(jpeg_content_sha256(&path).unwrap(), expected, "{name}");
            assert_eq!(
                jpeg_content_sha256_bytes(&std::fs::read(path).unwrap()).unwrap(),
                expected,
                "{name}"
            );
        }
    }
    const VECTORS: [(&str, &str); 2] = [
        (
            "IMG_0787.JPG",
            "fdc79d5549c0fa9190c422afc9ae506964904a328ff5c67ef6298cd5ead8e6b7",
        ),
        (
            "IMG_1039.JPG",
            "8cb0c2dfb0fb6a2bb7ecd28555dd49ada047b2bb45c53be4aeea7d56edc86b9d",
        ),
    ];
    fn fixture(name: &str) -> Vec<u8> {
        std::fs::read(format!("../fixtures/{name}")).unwrap()
    }
    fn segment(marker: u8) -> Vec<u8> {
        let body = b"metadata";
        [
            vec![0xff, marker],
            ((body.len() + 2) as u16).to_be_bytes().to_vec(),
            body.to_vec(),
        ]
        .concat()
    }
    fn inserted(data: &[u8], marker: u8) -> Vec<u8> {
        [&data[..2], &segment(marker), &data[2..]].concat()
    }

    struct ShortRead<R>(R);
    impl<R: Read> Read for ShortRead<R> {
        fn read(&mut self, buf: &mut [u8]) -> std::io::Result<usize> {
            let count = buf.len().min(1);
            self.0.read(&mut buf[..count])
        }
    }

    #[test]
    fn known_cross_language_hashes_and_short_reads() {
        for (name, expected) in VECTORS {
            let data = fixture(name);
            assert_eq!(
                jpeg_content_sha256_reader(ShortRead(Cursor::new(data))).unwrap(),
                expected
            );
        }
    }
    #[test]
    fn ignores_metadata_and_trailer() {
        for (name, expected) in VECTORS {
            let data = fixture(name);
            for marker in [0xe1, 0xed, 0xfe] {
                assert_eq!(
                    jpeg_content_sha256_bytes(&inserted(&data, marker)).unwrap(),
                    expected
                );
            }
            assert_eq!(
                jpeg_content_sha256_bytes(&[data, b"trailer".to_vec()].concat()).unwrap(),
                expected
            );
        }
        let data = fixture(VECTORS[0].0);
        assert_ne!(
            jpeg_content_sha256_bytes(&inserted(&data, 0xe2)).unwrap(),
            VECTORS[0].1
        );
    }
    #[test]
    fn rejects_bad_input() {
        assert!(jpeg_content_sha256_bytes(b"not jpeg").is_err());
    }
}
