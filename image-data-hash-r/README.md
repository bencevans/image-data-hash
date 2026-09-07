# imageDataHash for R

Native, in-memory JPEG ImageDataHash. R package name: `imageDataHash`.
Runtime dependency: `digest`.

## Installation from GitHub

Install the tagged release from GitHub (the package is not on CRAN):

```r
install.packages("remotes")
remotes::install_github(
  "bencevans/image-data-hash",
  subdir = "image-data-hash-r",
  ref = "v0.1.0"
)
```

This also installs the runtime dependency, `digest`.

## Installation from a local checkout

Install `digest` with `install.packages("digest")`, then from the repository root:

```sh
R CMD INSTALL image-data-hash-r
```

For direct use without installation, source `image-data-hash-r/R/image_data_hash.R`.

## Usage

```r
library(imageDataHash)

md5 <- image_data_hash("photo.jpg")
sha256 <- image_data_hash("photo.jpg", algorithm = "sha256")
sha512 <- image_data_hash("photo.jpg", algorithm = "sha512")

data <- readBin("photo.jpg", "raw", n = file.info("photo.jpg")$size)
digest <- image_data_hash_raw(data, algorithm = "sha256")
```

MD5 is the default. Names are case-insensitive and accept hyphens.
Results are lowercase hexadecimal strings. Invalid input or unsupported
algorithms raise an R error.

R does not offer a streaming API: it reads one JPEG into memory, selects scan
byte ranges, and hashes them with `digest`. Memory use is proportional to image
size; process large collections one image at a time. No temporary files or
external processes are used.

## Tests

Generate the [shared fixtures](https://github.com/bencevans/image-data-hash/blob/main/fixtures/README.md), install `testthat`, then:

```sh
cd image-data-hash-r
Rscript -e 'testthat::test_file("test_image_data_hash.R", reporter = "stop")'
```

Run `Rscript format.R` to apply the R formatter. See [compatibility rules](https://github.com/bencevans/image-data-hash/blob/main/SPEC.md).

## Project

Repository: [bencevans/image-data-hash](https://github.com/bencevans/image-data-hash). Maintainer: Ben Evans. Licensed under MIT.
