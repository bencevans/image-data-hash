library(imageDataHash)

# A minimal parser vector: SOI, an empty SOS header, scan bytes, and EOI.
# This tests byte selection, not whether a decoder can display the image.
scan <- as.raw(c(255, 218, 0, 2, 17, 34, 51))
jpeg <- c(as.raw(c(255, 216)), scan, as.raw(c(255, 217)))

for (algorithm in c("md5", "sha256", "sha512")) {
  expected <- digest::digest(scan, algo = algorithm, serialize = FALSE)
  stopifnot(identical(image_data_hash_raw(jpeg, algorithm), expected))

  # Inserting an APP1 metadata segment must not change the hash.
  metadata <- as.raw(c(255, 225, 0, 4, 65, 66))
  annotated <- c(jpeg[1:2], metadata, jpeg[-(1:2)])
  stopifnot(identical(image_data_hash_raw(annotated, algorithm), expected))
}
