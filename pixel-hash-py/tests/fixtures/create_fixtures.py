from pathlib import Path
import numpy as np
from PIL import Image

FIXTURES_DIR = Path(__file__).parent

def create_test_images():
    # Ensure fixtures directory exists
    # FIXTURES_DIR.mkdir(exist_ok=True)

    # Create RGB image with gradient
    rgb_array = np.zeros((100, 100, 3), dtype=np.uint8)
    for i in range(100):
        for j in range(100):
            rgb_array[i, j] = [i * 255//100, j * 255//100, 128]
    rgb_image = Image.fromarray(rgb_array, 'RGB')
    rgb_image.save(FIXTURES_DIR / 'gradient_rgb.png')

    # Create same image in different formats
    rgb_image.save(FIXTURES_DIR / 'gradient_rgb.jpg', quality=95)
    rgb_image.save(FIXTURES_DIR / 'gradient_rgb.bmp')

    # Create RGBA image with transparency gradient
    rgba_array = np.zeros((100, 100, 4), dtype=np.uint8)
    for i in range(100):
        for j in range(100):
            rgba_array[i, j] = [255, 0, 0, int(i * 255/100)]
    rgba_image = Image.fromarray(rgba_array, 'RGBA')
    rgba_image.save(FIXTURES_DIR / 'gradient_rgba.png')

    # Create grayscale image with gradient
    gray_array = np.zeros((100, 100), dtype=np.uint8)
    for i in range(100):
        gray_array[i, :] = i * 255//100
    gray_image = Image.fromarray(gray_array, 'L')
    gray_image.save(FIXTURES_DIR / 'gradient_gray.png')

    # Create binary image with pattern
    binary_array = np.zeros((100, 100), dtype=np.uint8)
    binary_array[::2, ::2] = 255
    binary_image = Image.fromarray(binary_array, 'L').convert('1')
    binary_image.save(FIXTURES_DIR / 'pattern_binary.png')

    # Create CMYK image
    cmyk_image = rgb_image.convert('CMYK')
    cmyk_image.save(FIXTURES_DIR / 'gradient_cmyk.tiff')

    # Create YCbCr image
    ycbcr_image = rgb_image.convert('YCbCr')
    ycbcr_image.save(FIXTURES_DIR / 'gradient_ycbcr.tiff')

    # Create images with different sizes
    rgb_image_small = rgb_image.resize((50, 50))
    rgb_image_small.save(FIXTURES_DIR / 'gradient_rgb_small.png')

    rgb_image_large = rgb_image.resize((200, 200))
    rgb_image_large.save(FIXTURES_DIR / 'gradient_rgb_large.png')

if __name__ == '__main__':
    create_test_images()
