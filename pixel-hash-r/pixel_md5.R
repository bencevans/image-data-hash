library(magick)
library(digest)

pixel_md5 <- function(image_ref) {
  # Accept either a magick image object or file path
  if (inherits(image_ref, "magick-image")) {
    img <- image_ref
  } else if (is.character(image_ref)) {
    img <- image_read(image_ref)
  } else {
    stop("image_ref must be a magick-image or a file path")
  }

  # Get raw pixel data
  raw_pixels <- as.integer(image_data(img, channels = "rgba"))
  size <- image_info(img)[, c("width", "height")]
  mode <- image_info(img)[, "colorspace"]

  # Hash: mode + size + pixels
  meta <- paste(mode, paste(size, collapse = "x"))
  digest(c(meta, raw_pixels), algo = "md5", serialize = FALSE)
}
