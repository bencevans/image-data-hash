"""Generate real metadata edits; never modify the original camera images.

Usage: python3 fixtures/generate.py OUTPUT_DIRECTORY
The output manifest contains paths relative to OUTPUT_DIRECTORY and fixed hashes.
"""
import argparse
import csv
import json
from pathlib import Path
import shutil
import subprocess

ORIGINALS = {
    "IMG_0787.JPG": "fdc79d5549c0fa9190c422afc9ae506964904a328ff5c67ef6298cd5ead8e6b7",
    "IMG_1039.JPG": "8cb0c2dfb0fb6a2bb7ecd28555dd49ada047b2bb45c53be4aeea7d56edc86b9d",
}
EDITS = {
    "timestamps": {"EXIF:DateTimeOriginal": "2026:09:05 12:34:56"},
    "gps": {"EXIF:GPSLatitude": "51.5", "EXIF:GPSLatitudeRef": "N", "EXIF:GPSLongitude": "0.12", "EXIF:GPSLongitudeRef": "W"},
    "orientation": {"EXIF:Orientation#": "6"},
    "description": {"EXIF:ImageDescription": "Leopard observed near the river"},
    "copyright": {"EXIF:Copyright": "Camera trap research 2026"},
    "exif_species": {"EXIF:UserComment": "Species: Panthera pardus"},
    "iptc_species": {"IPTC:Keywords": "Panthera pardus"},
    "xmp_species": {"XMP-dc:Subject": "Panthera pardus"},
    "large_xmp": {"XMP-dc:Description": "camera trap annotation " * 4000},
    "comment": {"Comment": "Species identification reviewed"},
}


def edit(path, arguments):
    subprocess.run(["exiftool", "-overwrite_original", *arguments, str(path)],
                   check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("Output directory must be empty")
    rows = []
    for name, expected in ORIGINALS.items():
        original = Path(__file__).parent / name
        for variant, tags in EDITS.items():
            target = output / f"{original.stem}-{variant}.JPG"
            shutil.copyfile(original, target)
            edit(target, [f"-{tag}={value}" for tag, value in tags.items()])
            # Verify edits really happened, rather than silently accepting an
            # unsupported ExifTool tag. Read values back in numeric form.
            metadata = json.loads(subprocess.check_output(
                ["exiftool", "-j", "-n", *[f"-{tag.rstrip('#')}" for tag in tags], str(target)]))[0]
            for tag in tags:
                key = tag.split(":")[-1].rstrip("#")
                if key not in metadata:
                    raise RuntimeError(f"Missing edited tag {tag} in {target}")
            if target.read_bytes() == original.read_bytes():
                raise RuntimeError(f"Edit did not change {target}")
            rows.append((target.name, expected))
        # Removal, replacement, and thumbnail edits exercise existing EXIF.
        for variant, args in {
            "remove_exif": ["-EXIF:all="],
            "remove_thumbnail": ["-ThumbnailImage="],
            "replace_thumbnail": [f"-ThumbnailImage<={Path(__file__).parent.parent / 'pixel-hash-py/tests/fixtures/gradient_rgb.jpg'}"],
            "remove_ignored": ["-EXIF:all=", "-XMP:all=", "-IPTC:all=", "-Comment="],
            "combined": ["-EXIF:Orientation#=3", "-IPTC:Keywords=elephant", "-XMP-dc:Subject=elephant", "-Comment=reviewed"],
        }.items():
            target = output / f"{original.stem}-{variant}.JPG"
            shutil.copyfile(original, target)
            edit(target, args)
            if target.read_bytes() == original.read_bytes():
                raise RuntimeError(f"Edit did not change {target}")
            rows.append((target.name, expected))
    with (output / "manifest.tsv").open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(["file", "sha256"])
        writer.writerows(rows)
    print(f"Generated {len(rows)} variants in {output}")


if __name__ == "__main__":
    main()
