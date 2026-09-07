//! Native JPEG hashing compatible with ExifTool's ImageDataHash.
//! Only MD5, SHA-256 and SHA-512 are supported; MD5 is the default.

use anyhow::{Result, bail};
use md5::Md5;
use sha2::{Digest, Sha256, Sha512};
use std::fs::File;
use std::io::{BufReader, Cursor, Read};
use std::path::Path;

const MARKER_PREFIX: u8 = 0xff;
const START_OF_SCAN: u8 = 0xda;
const END_OF_IMAGE: u8 = 0xd9;
const BUFFER_SIZE: usize = 65536;

// ExifTool treats SOS as lengthless, so its header joins the scan bytes.
fn has_length_field(marker: u8) -> bool {
    !matches!(marker, 0 | 1 | 0xd0..=0xda)
}

fn starts_hash_chunk(marker: u8) -> bool {
    matches!(marker, 0 | START_OF_SCAN | 0xd0..=0xd7)
}

#[derive(Clone, Copy, Debug, Default)]
/// Hash algorithms supported by ExifTool's ImageDataHash option.
pub enum Algorithm {
    /// MD5: 32 lowercase hexadecimal characters (the ExifTool default).
    #[default]
    Md5,
    /// SHA-256: 64 lowercase hexadecimal characters.
    Sha256,
    /// SHA-512: 128 lowercase hexadecimal characters.
    Sha512,
}

/// Hash a path with ExifTool's default algorithm (MD5).
///
/// Returns a lowercase hexadecimal digest. The file is closed on completion.
///
/// # Errors
/// Returns an error if the file cannot be read or the JPEG is malformed.
pub fn image_data_hash(path: impl AsRef<Path>) -> Result<String> {
    image_data_hash_with_algorithm(path, Algorithm::Md5)
}

/// Hash a JPEG path with the selected algorithm, closing the file afterwards.
///
/// # Errors
/// Returns an error for I/O failures or malformed/truncated JPEG input.
pub fn image_data_hash_with_algorithm(
    path: impl AsRef<Path>,
    algorithm: Algorithm,
) -> Result<String> {
    image_data_hash_reader(File::open(path)?, algorithm)
}

/// Hash JPEG bytes, ignoring any trailer after the end-of-image marker.
///
/// Returns a lowercase hexadecimal digest; the input bytes are borrowed.
///
/// # Errors
/// Returns an error if the JPEG is malformed or truncated.
pub fn image_data_hash_bytes(data: &[u8], algorithm: Algorithm) -> Result<String> {
    image_data_hash_reader(Cursor::new(data), algorithm)
}

/// Hash a reader without loading the image into memory.
///
/// Pass `Algorithm::default()` for MD5. The reader is buffered internally and
/// may be consumed past EOI. Pass `&mut reader` to retain ownership, but do not
/// rely on its final position. Returns a lowercase hexadecimal digest.
///
/// # Errors
/// Returns an error for failed reads or malformed/truncated JPEG input.
pub fn image_data_hash_reader(reader: impl Read, algorithm: Algorithm) -> Result<String> {
    match algorithm {
        Algorithm::Md5 => hash_jpeg::<_, Md5>(reader),
        Algorithm::Sha256 => hash_jpeg::<_, Sha256>(reader),
        Algorithm::Sha512 => hash_jpeg::<_, Sha512>(reader),
    }
}

fn read_byte(reader: &mut impl Read) -> Result<u8> {
    let mut byte = [0];
    reader.read_exact(&mut byte)?;
    Ok(byte[0])
}

fn hash_jpeg<R: Read, H: Digest + Clone>(reader: R) -> Result<String> {
    let mut reader = BufReader::new(reader);
    let mut signature = [0; 2];
    reader.read_exact(&mut signature)?;
    if signature != [255, 216] {
        bail!("not a JPEG file");
    }

    let mut digest = H::new();
    let mut candidate: Option<H> = None;
    let mut found_scan = false;
    let mut buffer = [0u8; BUFFER_SIZE];

    loop {
        // A scan chunk becomes part of the hash only when its terminating
        // marker has no length field. Clone the digest so it can be discarded.
        let mut used = 0;
        loop {
            let byte = read_byte(&mut reader)?;
            if byte == MARKER_PREFIX {
                break;
            }
            buffer[used] = byte;
            used += 1;
            if used == buffer.len() {
                if let Some(ref mut pending) = candidate {
                    pending.update(&buffer);
                }
                used = 0;
            }
        }
        if let Some(ref mut pending) = candidate {
            pending.update(&buffer[..used]);
        }

        let mut fill_count = 0;
        let code = loop {
            let byte = read_byte(&mut reader)?;
            if byte != MARKER_PREFIX {
                break byte;
            }
            fill_count += 1;
        };
        let standalone = !has_length_field(code);
        if standalone {
            if let Some(mut pending) = candidate.take() {
                // All FF fill bytes except the final marker prefix belong
                // to the preceding chunk.
                buffer.fill(MARKER_PREFIX);
                while fill_count > 0 {
                    let count = fill_count.min(buffer.len());
                    pending.update(&buffer[..count]);
                    fill_count -= count;
                }
                digest = pending;
            }
        }
        candidate = None;

        if code == END_OF_IMAGE {
            if !found_scan {
                bail!("JPEG has no SOS");
            }
            return Ok(digest
                .finalize()
                .iter()
                .map(|byte| format!("{byte:02x}"))
                .collect());
        }
        if code == START_OF_SCAN {
            found_scan = true;
        }
        if starts_hash_chunk(code) {
            let mut pending = digest.clone();
            pending.update([MARKER_PREFIX, code]);
            candidate = Some(pending);
        }

        if !standalone {
            let mut length_bytes = [0; 2];
            reader.read_exact(&mut length_bytes)?;
            let length = u16::from_be_bytes(length_bytes) as usize;
            if length < 2 {
                bail!("invalid JPEG segment length");
            }
            // Skip metadata and tables, without seeking (pipes work too).
            let mut remaining = length - 2;
            while remaining > 0 {
                let count = remaining.min(buffer.len());
                reader.read_exact(&mut buffer[..count])?;
                remaining -= count;
            }
        }
    }
}
