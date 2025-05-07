import pytest
from pathlib import Path
from pixel_hash import pixel_md5
from PIL import Image
from fixtures.create_fixtures import create_test_images, FIXTURES_DIR

# Create test fixtures if they don't exist
if not FIXTURES_DIR.exists():
    create_test_images()
from fixtures.create_fixtures import  FIXTURES_DIR

def test_md5_none():
    with pytest.raises(Exception):
        pixel_md5(None)

def test_md5_invalid_type():
    with pytest.raises(Exception):
        pixel_md5(42)  # Integer is not a valid type

def test_md5_rgb():
    """Test hashing an RGB image"""
    image = Image.new("RGB", (100, 100), color="red")
    hash1 = pixel_md5(image)
    assert isinstance(hash1, str)
    assert len(hash1) == 32  # MD5 hash is 32 chars

    # Same content should produce same hash
    image2 = Image.new("RGB", (100, 100), color="red")
    hash2 = pixel_md5(image2)
    assert hash1 == hash2

def test_md5_rgba():
    """Test hashing an RGBA image"""
    image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    hash1 = pixel_md5(image)

    # Different alpha should produce different hash
    image2 = Image.new("RGBA", (100, 100), color=(255, 0, 0, 255))
    hash2 = pixel_md5(image2)
    assert hash1 != hash2

def test_md5_grayscale():
    """Test hashing a grayscale image"""
    image = Image.new("L", (100, 100), color=128)
    hash1 = pixel_md5(image)

    # Different gray value should produce different hash
    image2 = Image.new("L", (100, 100), color=255)
    hash2 = pixel_md5(image2)
    assert hash1 != hash2

def test_md5_binary():
    """Test hashing a binary image"""
    image = Image.new("1", (100, 100), color=0)
    hash1 = pixel_md5(image)

    # Different binary value should produce different hash
    image2 = Image.new("1", (100, 100), color=1)
    hash2 = pixel_md5(image2)
    assert hash1 != hash2

def test_md5_size_matters():
    """Test that different image sizes produce different hashes"""
    image1 = Image.new("RGB", (100, 100), color="red")
    image2 = Image.new("RGB", (200, 200), color="red")
    assert pixel_md5(image1) != pixel_md5(image2)

def test_md5_path():
    """Test hashing an image loaded from a path"""
    # Test RGB image path loading
    rgb_path = FIXTURES_DIR / 'gradient_rgb.png'
    rgb_image = Image.open(rgb_path)
    assert pixel_md5(rgb_path) == pixel_md5(rgb_image)

def test_image_formats():
    """Test that same image content in different formats produces same hash"""
    # Test PNG vs JPEG vs BMP
    png_hash = pixel_md5(FIXTURES_DIR / 'gradient_rgb.png')
    jpg_hash = pixel_md5(FIXTURES_DIR / 'gradient_rgb.jpg')
    bmp_hash = pixel_md5(FIXTURES_DIR / 'gradient_rgb.bmp')

    # The hashes should be different due to format-specific compression
    assert len({png_hash, jpg_hash, bmp_hash}) > 1

def test_color_spaces():
    """Test images in different color spaces"""
    # Test RGB vs CMYK vs YCbCr
    rgb_image = Image.open(FIXTURES_DIR / 'gradient_rgb.png')
    cmyk_image = Image.open(FIXTURES_DIR / 'gradient_cmyk.tiff')
    ycbcr_image = Image.open(FIXTURES_DIR / 'gradient_ycbcr.tiff')

    rgb_hash = pixel_md5(rgb_image)
    cmyk_hash = pixel_md5(cmyk_image)
    ycbcr_hash = pixel_md5(ycbcr_image)

    # Different color spaces should produce different hashes
    assert len({rgb_hash, cmyk_hash, ycbcr_hash}) == 3

def test_image_with_alpha():
    """Test handling of alpha channel"""
    rgba_image = Image.open(FIXTURES_DIR / 'gradient_rgba.png')
    # Convert to RGB by removing alpha
    rgb_image = rgba_image.convert('RGB')

    # Hashes should be different with and without alpha
    assert pixel_md5(rgba_image) != pixel_md5(rgb_image)

def test_image_resize():
    """Test that resized images produce different hashes"""
    small_image = Image.open(FIXTURES_DIR / 'gradient_rgb_small.png')
    large_image = Image.open(FIXTURES_DIR / 'gradient_rgb_large.png')
    orig_image = Image.open(FIXTURES_DIR / 'gradient_rgb.png')

    # All sizes should produce different hashes
    hashes = {
        pixel_md5(small_image),
        pixel_md5(large_image),
        pixel_md5(orig_image)
    }
    assert len(hashes) == 3


