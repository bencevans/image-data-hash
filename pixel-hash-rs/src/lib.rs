use std::fs::File;
use std::io::BufReader;
use std::path::Path;

use anyhow::{Result, bail};
use image::{DynamicImage, GenericImageView, ImageFormat};

fn pixel_md5<P: AsRef<Path>>(image_ref: P) -> Result<String> {
    let path = image_ref.as_ref();

    // Open the image
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let format = image::guess_format(&std::fs::read(path)?)?;
    let img = image::load(reader, format)?;

    hash_image(&img)
}

fn hash_image(img: &DynamicImage) -> Result<String> {
    // Get pixel bytes in raw RGBA or native format
    let pixel_bytes = img.as_bytes();  // Get bytes without moving

    // Include mode (ColorType) and size
    let color_type = img.color();
    let dimensions = img.dimensions();
    let meta_info = format!("{:?}_{:?}", color_type, dimensions);

    // MD5 hash of metadata + pixel bytes
    let mut hasher = md5::Context::new();
    hasher.consume(meta_info.as_bytes());
    hasher.consume(&pixel_bytes);
    let hash = hasher.compute();

    Ok(format!("{:x}", hash))
}

#[cfg(test)]
mod tests {
    use super::*;

    // use crate::pixel_md5::{hash_image, pixel_md5};
    use image::open;
    use std::collections::HashSet;
    use std::path::PathBuf;

    fn fixtures_dir() -> PathBuf {
        PathBuf::from("../pixel-hash-py/tests/fixtures")
    }

    #[test]
    fn test_md5_path() {
        let dir = fixtures_dir();
        let path = dir.join("gradient_rgb.png");
        let img = open(&path).unwrap();

        let hash1 = pixel_md5(&path).unwrap();
        let hash2 = hash_image(&img).unwrap();

        assert_eq!(hash1, hash2);
    }

    #[test]
    fn test_image_formats() {
        let dir = fixtures_dir();
        let png = pixel_md5(dir.join("gradient_rgb.png")).unwrap();
        let jpg = pixel_md5(dir.join("gradient_rgb.jpg")).unwrap();
        let bmp = pixel_md5(dir.join("gradient_rgb.bmp")).unwrap();

        let unique: HashSet<_> = vec![png, jpg, bmp].into_iter().collect();
        assert!(
            unique.len() > 1,
            "Expected different hashes due to format compression differences"
        );
    }

    #[test]
    fn test_color_spaces() {
        let dir = fixtures_dir();
        let rgb = pixel_md5(dir.join("gradient_rgb.png")).unwrap();
        let cmyk = pixel_md5(dir.join("gradient_cmyk.tiff")).unwrap();
        let ycbcr = pixel_md5(dir.join("gradient_ycbcr.tiff")).unwrap();

        let unique: HashSet<_> = vec![rgb, cmyk, ycbcr].into_iter().collect();
        assert_eq!(
            unique.len(),
            3,
            "Each color space should yield a unique hash"
        );
    }

    #[test]
    fn test_image_with_alpha() {
        let dir = fixtures_dir();
        let rgba_img = image::open(dir.join("gradient_rgba.png")).unwrap();
        let rgb_img = rgba_img.clone().into_rgb8();
        let rgb_img = image::DynamicImage::ImageRgb8(rgb_img);

        let hash_rgba = hash_image(&rgba_img).unwrap();
        let hash_rgb = hash_image(&rgb_img).unwrap();

        assert_ne!(
            hash_rgba, hash_rgb,
            "RGB and RGBA versions should yield different hashes"
        );
    }

    #[test]
    fn test_image_resize() {
        let dir = fixtures_dir();
        let small = pixel_md5(dir.join("gradient_rgb_small.png")).unwrap();
        let large = pixel_md5(dir.join("gradient_rgb_large.png")).unwrap();
        let original = pixel_md5(dir.join("gradient_rgb.png")).unwrap();

        let unique: HashSet<_> = vec![small, large, original].into_iter().collect();
        assert_eq!(
            unique.len(),
            3,
            "Different sizes should yield different hashes"
        );
    }
}
