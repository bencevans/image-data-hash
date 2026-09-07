use image_data_hash::{
    Algorithm, image_data_hash, image_data_hash_bytes, image_data_hash_reader,
    image_data_hash_with_algorithm,
};
use std::io::{Cursor, Read};
use std::path::PathBuf;

#[test]
fn matches_exiftool_for_every_fixture_and_algorithm() {
    let directory = PathBuf::from(
        std::env::var("JPEG_HASH_FIXTURES").unwrap_or_else(|_| "../fixtures/generated".into()),
    );
    let manifest = std::fs::read_to_string(directory.join("manifest.tsv")).unwrap();
    let rows: Vec<_> = manifest.lines().skip(1).collect();
    assert_eq!(rows.len(), 41);
    for row in rows {
        let columns: Vec<_> = row.split('\t').collect();
        let path = directory.join(columns[0]);
        let data = std::fs::read(&path).unwrap();
        assert_eq!(image_data_hash(&path).unwrap(), columns[1]);
        for (index, algorithm) in [Algorithm::Md5, Algorithm::Sha256, Algorithm::Sha512]
            .into_iter()
            .enumerate()
        {
            assert_eq!(
                image_data_hash_with_algorithm(&path, algorithm).unwrap(),
                columns[index + 1],
                "{}",
                columns[0]
            );
            assert_eq!(
                image_data_hash_bytes(&data, algorithm).unwrap(),
                columns[index + 1],
                "{}",
                columns[0]
            );
        }
        if columns[0].starts_with("structural") {
            let reader = ShortReader(Cursor::new(data));
            assert_eq!(
                image_data_hash_reader(reader, Algorithm::Md5).unwrap(),
                columns[1]
            );
        }
    }
}

struct ShortReader<R>(R);
impl<R: Read> Read for ShortReader<R> {
    fn read(&mut self, buffer: &mut [u8]) -> std::io::Result<usize> {
        let count = buffer.len().min(1);
        self.0.read(&mut buffer[..count])
    }
}

#[test]
fn rejects_invalid_input() {
    for data in [
        b"".as_slice(),
        b"not jpeg",
        b"\xff\xd8",
        b"\xff\xd8\xff\xe1\x00",
        b"\xff\xd8\xff\xe1\x00\x01",
        b"\xff\xd8\xff\xd9",
        b"\xff\xd8\xff\xda\x00\x02abc\xff",
    ] {
        assert!(image_data_hash_bytes(data, Algorithm::Md5).is_err());
    }
}
