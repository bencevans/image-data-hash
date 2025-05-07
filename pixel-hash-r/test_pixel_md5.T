library(testthat)
source("pixel_md5.R")

FIXTURES_DIR <- "tests/testthat/fixtures"

test_that("invalid input throws", {
  expect_error(pixel_md5(NULL))
  expect_error(pixel_md5(42))
})

test_that("RGB hashing", {
  img1 <- image_blank(100, 100, color = "red")
  img2 <- image_blank(100, 100, color = "red")
  hash1 <- pixel_md5(img1)
  hash2 <- pixel_md5(img2)
  expect_equal(nchar(hash1), 32)
  expect_equal(hash1, hash2)
})

test_that("RGBA differs by alpha", {
  img1 <- image_blank(100, 100, color = "#FF000080")
  img2 <- image_blank(100, 100, color = "#FF0000FF")
  expect_false(pixel_md5(img1) == pixel_md5(img2))
})

test_that("Grayscale difference", {
  img1 <- image_blank(100, 100, color = "gray50")
  img2 <- image_blank(100, 100, color = "gray90")
  expect_false(pixel_md5(img1) == pixel_md5(img2))
})

test_that("Binary images differ", {
  img1 <- image_blank(100, 100, color = "black")
  img2 <- image_blank(100, 100, color = "white")
  expect_false(pixel_md5(img1) == pixel_md5(img2))
})

test_that("Size matters", {
  img1 <- image_blank(100, 100, color = "red")
  img2 <- image_blank(200, 200, color = "red")
  expect_false(pixel_md5(img1) == pixel_md5(img2))
})

test_that("Path vs image identical", {
  path <- file.path(FIXTURES_DIR, "gradient_rgb.png")
  img <- image_read(path)
  expect_equal(pixel_md5(path), pixel_md5(img))
})

test_that("Formats differ", {
  png_hash <- pixel_md5(file.path(FIXTURES_DIR, "gradient_rgb.png"))
  jpg_hash <- pixel_md5(file.path(FIXTURES_DIR, "gradient_rgb.jpg"))
  bmp_hash <- pixel_md5(file.path(FIXTURES_DIR, "gradient_rgb.bmp"))
  expect_gt(length(unique(c(png_hash, jpg_hash, bmp_hash))), 1)
})

test_that("Color spaces differ", {
  hashes <- c(
    pixel_md5(file.path(FIXTURES_DIR, "gradient_rgb.png")),
    pixel_md5(file.path(FIXTURES_DIR, "gradient_cmyk.tiff")),
    pixel_md5(file.path(FIXTURES_DIR, "gradient_ycbcr.tiff"))
  )
  expect_equal(length(unique(hashes)), 3)
})

test_that("Alpha channel changes hash", {
  rgba <- image_read(file.path(FIXTURES_DIR, "gradient_rgba.png"))
  rgb <- image_convert(rgba, colorspace = "RGB")
  expect_false(pixel_md5(rgba) == pixel_md5(rgb))
})

test_that("Resizing changes hash", {
  hashes <- c(
    pixel_md5(file.path(FIXTURES_DIR, "gradient_rgb_small.png")),
    pixel_md5(file.path(FIXTURES_DIR, "gradient_rgb_large.png")),
    pixel_md5(file.path(FIXTURES_DIR, "gradient_rgb.png"))
  )
  expect_equal(length(unique(hashes)), 3)
})
