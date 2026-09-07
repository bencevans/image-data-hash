library(testthat)
source("R/image_data_hash.R")

directory <- Sys.getenv("JPEG_HASH_FIXTURES", "../fixtures/generated")
manifest <- read.delim(file.path(directory, "manifest.tsv"), stringsAsFactors = FALSE)

test_that("all fixtures match ExifTool for every algorithm", {
  expect_equal(nrow(manifest), 41L)
  for (i in seq_len(nrow(manifest))) {
    path <- file.path(directory, manifest$file[i])
    data <- readBin(path, "raw", n = file.info(path)$size)
    expect_equal(image_data_hash_raw(data), manifest$md5[i])
    for (algorithm in c("md5", "sha256", "sha512")) {
      expect_equal(image_data_hash(path, algorithm), manifest[[algorithm]][i], info = manifest$file[i])
      expect_equal(image_data_hash_raw(data, algorithm), manifest[[algorithm]][i], info = manifest$file[i])
    }
  }
})

test_that("algorithm aliases and invalid inputs", {
  path <- file.path(directory, manifest$file[1])
  expect_equal(image_data_hash(path, "SHA-256"), manifest$sha256[1])
  expect_equal(image_data_hash(path, "SHA-512"), manifest$sha512[1])
  expect_error(image_data_hash(path, "sha1"))
  expect_error(image_data_hash_raw("not bytes"))
  for (bytes in list(
    integer(), c(1, 2, 3, 4), c(255, 216), c(255, 216, 255, 217),
    c(255, 216, 255, 225, 0, 1), c(255, 216, 255, 218, 0, 2, 255)
  )) {
    expect_error(image_data_hash_raw(as.raw(bytes)))
  }
})
