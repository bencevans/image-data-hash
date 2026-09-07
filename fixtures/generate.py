"""Generate real metadata edits; never modify the original camera images.

Usage: python3 fixtures/generate.py OUTPUT_DIRECTORY
The output manifest contains relative paths and ExifTool reference hashes.
"""

import argparse
import csv
import json
from pathlib import Path
import shutil
import subprocess

ORIGINALS = ("IMG_0787.JPG", "IMG_1039.JPG")
EDITS = {
    "timestamps": {"EXIF:DateTimeOriginal": "2026:09:05 12:34:56"},
    "gps": {
        "EXIF:GPSLatitude": "51.5",
        "EXIF:GPSLatitudeRef": "N",
        "EXIF:GPSLongitude": "0.12",
        "EXIF:GPSLongitudeRef": "W",
    },
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
    subprocess.run(
        ["exiftool", "-overwrite_original", *arguments, str(path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    output = parser.parse_args().output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("Output directory must be empty")
    rows = []
    for name in ORIGINALS:
        original = Path(__file__).parent / name
        shutil.copyfile(original, output / name)
        rows.append((name, name))
        for variant, tags in EDITS.items():
            target = output / f"{original.stem}-{variant}.JPG"
            shutil.copyfile(original, target)
            edit(target, [f"-{tag}={value}" for tag, value in tags.items()])
            # Verify edits really happened, rather than silently accepting an
            # unsupported ExifTool tag. Read values back in numeric form.
            metadata = json.loads(
                subprocess.check_output(
                    [
                        "exiftool",
                        "-j",
                        "-n",
                        *[f"-{tag.rstrip('#')}" for tag in tags],
                        str(target),
                    ]
                )
            )[0]
            for tag in tags:
                key = tag.split(":")[-1].rstrip("#")
                if key not in metadata:
                    raise RuntimeError(f"Missing edited tag {tag} in {target}")
            if target.read_bytes() == original.read_bytes():
                raise RuntimeError(f"Edit did not change {target}")
            rows.append((target.name, name))
        # Removal, replacement, and thumbnail edits exercise existing EXIF.
        for variant, args in {
            "remove_exif": ["-EXIF:all="],
            "remove_thumbnail": ["-ThumbnailImage="],
            "replace_thumbnail": [
                f"-ThumbnailImage<={Path(__file__).parent.parent / 'image-data-hash-py/tests/fixtures/gradient_rgb.jpg'}"
            ],
            "remove_ignored": ["-EXIF:all=", "-XMP:all=", "-IPTC:all=", "-Comment="],
            "combined": [
                "-EXIF:Orientation#=3",
                "-IPTC:Keywords=elephant",
                "-XMP-dc:Subject=elephant",
                "-Comment=reviewed",
            ],
        }.items():
            target = output / f"{original.stem}-{variant}.JPG"
            shutil.copyfile(original, target)
            edit(target, args)
            if target.read_bytes() == original.read_bytes():
                raise RuntimeError(f"Edit did not change {target}")
            rows.append((target.name, name))

    # Real baseline, progressive and restart-marker JPEGs from the same pixels.
    pixels = bytes(
        (x * 17 + y * 31 + channel * 53) % 256
        for y in range(32)
        for x in range(32)
        for channel in range(3)
    )
    ppm = b"P6\n32 32\n255\n" + pixels
    for label, options in {
        "baseline": [],
        "progressive": ["-progressive"],
        "restart": ["-restart", "1B"],
    }.items():
        target = output / f"encoded-{label}.JPG"
        target.write_bytes(subprocess.check_output(["cjpeg", *options], input=ppm))
        rows.append((target.name, None))

    # Small structural vectors expose the chunk-selection behavior of ExifTool.
    # They are parser tests, not necessarily decodable photographs.
    scan = b"\xff\xda\x00\x02abc\xff\x00def"
    for label, body in {
        "stuffing": scan,
        "restart": scan + b"\xff\xd0ghi",
        "fill": scan + b"\xff",
        "multiple-scans": scan + b"\xff\xda\x00\x02xyz",
        "between-scans": scan + b"\xff\xfe\x00\x05hey" + scan,
        "changed-scan": scan + b"changed",
    }.items():
        target = output / f"structural-{label}.JPG"
        target.write_bytes(b"\xff\xd8" + body + b"\xff\xd9")
        rows.append((target.name, None))

    hashes = {}
    for algorithm in ("md5", "sha256", "sha512"):
        records = json.loads(
            subprocess.check_output(
                [
                    "exiftool",
                    "-j",
                    "-ImageDataHash",
                    "-api",
                    f"ImageHashType={algorithm.upper()}",
                    *[str(output / name) for name, _ in rows],
                ]
            )
        )
        hashes[algorithm] = {
            Path(record["SourceFile"]).name: record["ImageDataHash"]
            for record in records
        }
        for name, original in rows:
            if original and hashes[algorithm][name] != hashes[algorithm][original]:
                raise RuntimeError(f"ExifTool hash changed after metadata edit: {name}")

    with (output / "manifest.tsv").open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(["file", "md5", "sha256", "sha512"])
        for name, _ in rows:
            writer.writerow([name, *[hashes[algo][name] for algo in hashes]])
    (output / "exiftool-version.txt").write_text(
        subprocess.check_output(["exiftool", "-ver"], text=True)
    )
    print(f"Generated {len(rows)} variants in {output}")


if __name__ == "__main__":
    main()
