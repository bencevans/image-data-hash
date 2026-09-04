library(testthat)
source("jpeg_content_sha256.R")

test_that("scan offsets preserve stuffing, restarts and multiple scans", {
  # Structural parser vector, not a decodable photograph. APP1 occurs between scans.
  first <- as.raw(c(255, 216, 255, 218, 0, 2, 10, 255, 0, 20, 255, 208, 30))
  second <- as.raw(c(255, 218, 0, 2, 40, 255, 255, 217))
  metadata <- as.raw(c(255, 225, 0, 5, 1, 2, 3))
  canonical <- c(first, second)
  expect_identical(.canonical_jpeg(c(first, metadata, second, as.raw(99))), canonical)
  expect_equal(jpeg_content_sha256_raw(c(first, metadata, second)),
               digest::digest(canonical, algo = "sha256", serialize = FALSE))
  expect_error(jpeg_content_sha256_raw(first), "EOI")
  expect_error(jpeg_content_sha256_raw(c(first, as.raw(255))), "truncated JPEG marker")
})

test_that("shared generated EXIF variants match fixed hashes", {
  directory <- Sys.getenv("JPEG_HASH_FIXTURES", "../fixtures/generated")
  manifest <- read.delim(file.path(directory, "manifest.tsv"), stringsAsFactors = FALSE)
  expect_equal(nrow(manifest), 30L)
  for (i in seq_len(nrow(manifest))) {
    path <- file.path(directory, manifest$file[i])
    expect_equal(jpeg_content_sha256(path), manifest$sha256[i], info = manifest$file[i])
    expect_equal(jpeg_content_sha256_raw(readBin(path, "raw", n = file.info(path)$size)), manifest$sha256[i], info = manifest$file[i])
  }
})

vectors <- c(
  "IMG_0787.JPG" = "fdc79d5549c0fa9190c422afc9ae506964904a328ff5c67ef6298cd5ead8e6b7",
  "IMG_1039.JPG" = "8cb0c2dfb0fb6a2bb7ecd28555dd49ada047b2bb45c53be4aeea7d56edc86b9d"
)
segment <- function(marker, payload) {
  body <- charToRaw(payload); len <- length(body) + 2L
  as.raw(c(255L, marker, bitwShiftR(len, 8), bitwAnd(len, 255L), as.integer(body)))
}
insert <- function(data, marker) c(data[1:2], segment(marker, "metadata"), data[3:length(data)])

test_that("known cross-language hashes", {
  for (name in names(vectors)) expect_equal(jpeg_content_sha256(file.path("../fixtures", name)), unname(vectors[name]))
})
test_that("metadata is ignored but ICC is retained", {
  for (name in names(vectors)) {
    fixture <- file.path("../fixtures", name); data <- readBin(fixture, "raw", n = file.info(fixture)$size)
    hash <- unname(vectors[name])
    for (marker in c(225L, 237L, 254L)) expect_equal(jpeg_content_sha256_raw(insert(data, marker)), hash)
    expect_equal(jpeg_content_sha256_raw(c(data, charToRaw("vendor trailer"))), hash)
  }
  fixture <- file.path("../fixtures", names(vectors)[1]); data <- readBin(fixture, "raw", n = file.info(fixture)$size)
  expect_false(jpeg_content_sha256_raw(insert(data, 226L)) == unname(vectors[1]))
})
test_that("malformed input is rejected", expect_error(jpeg_content_sha256_raw(charToRaw("not jpeg"))))
