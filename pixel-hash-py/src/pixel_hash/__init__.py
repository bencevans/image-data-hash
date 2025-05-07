from pathlib import Path
from typing import Union
from PIL import Image
from hashlib import md5
import numpy as np

def pixel_md5(image_ref : Union[Image.Image, Path]) -> str:
    """
    Hashes
    """
    if isinstance(image_ref, Image.Image):
        image = image_ref
    elif isinstance(image_ref, (Path, str)):
        image = Image.open(image_ref)
    else:
        raise Exception("image_ref must be a str, pathlib.Path or PIL.Image instance")


    # Load the image fully (decode it), but do not convert color space
    image.load()  # Ensure data is read

    # Extract pixel data in native format
    pixel_array = np.array(img)
    pixel_bytes = pixel_array.tobytes()

    # Combine with mode and size to ensure format matters
    meta_info = f"{image.mode}_{image.size}".encode()

    # Hash pixel data + mode + size
    hash_digest = md5(meta_info + pixel_bytes).hexdigest()

    return hash_digest
