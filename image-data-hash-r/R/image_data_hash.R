# Select JPEG scan chunks using the same rules as ExifTool's ImageDataHash.
# This is an in-memory parser; callers should process one image at a time.
.image_data <- function(data) {
  byte_count <- length(data)
  signature <- as.raw(c(255, 216))
  if (byte_count < 4 || !identical(data[1:2], signature)) {
    stop("not a JPEG file")
  }

  # Find all FF bytes at once, avoiding an interpreted loop over every pixel byte.
  marker_offsets <- which(data == as.raw(255))
  position <- 3
  previous_marker <- 216L
  chunk_start <- 1
  found_scan <- FALSE
  chunks <- list()

  while (position <= byte_count) {
    next_index <- findInterval(position - 1, marker_offsets) + 1L
    if (next_index > length(marker_offsets)) {
      stop("JPEG has no EOI")
    }

    position <- marker_offsets[next_index]
    while (position <= byte_count && data[position] == as.raw(255)) {
      position <- position + 1
    }
    if (position > byte_count) {
      stop("truncated JPEG marker")
    }

    marker <- as.integer(data[position])
    position <- position + 1
    standalone <- marker %in% c(0L, 1L, 208L:218L)
    eligible <- previous_marker %in% c(0L, 218L, 208L:215L)

    if (eligible && standalone) {
      # The final FF and marker code start the next chunk. Earlier fill bytes
      # are included in this one. Length-bearing markers discard the candidate.
      chunk_end <- position - 3
      chunks[[length(chunks) + 1L]] <- data[chunk_start:chunk_end]
    }

    if (marker == 217L) {
      if (!found_scan) {
        stop("JPEG has no SOS")
      }
      if (!length(chunks)) {
        return(raw())
      }
      return(do.call(c, chunks))
    }
    if (marker == 218L) {
      found_scan <- TRUE
    }

    chunk_start <- position - 2
    previous_marker <- marker
    if (!standalone) {
      if (position + 1 > byte_count) {
        stop("truncated JPEG segment length")
      }
      segment_length <- as.integer(data[position]) * 256L +
        as.integer(data[position + 1])
      if (segment_length < 2 || position + segment_length - 1 > byte_count) {
        stop("invalid JPEG segment length")
      }
      position <- position + segment_length
    }
  }
  stop("JPEG has no EOI")
}

# Hash raw JPEG bytes. Algorithm spelling accepts MD5, SHA256, SHA-256, etc.
image_data_hash_raw <- function(data, algorithm = "md5") {
  if (!is.raw(data)) {
    stop("data must be a raw vector")
  }
  if (!is.character(algorithm) || length(algorithm) != 1L || is.na(algorithm)) {
    stop("invalid algorithm")
  }
  algorithm <- gsub("-", "", tolower(algorithm), fixed = TRUE)
  if (!(algorithm %in% c("md5", "sha256", "sha512"))) {
    stop("unsupported hash algorithm")
  }
  digest::digest(.image_data(data), algo = algorithm, serialize = FALSE)
}

# Read one JPEG file and return its lowercase hexadecimal image-data hash.
image_data_hash <- function(path, algorithm = "md5") {
  if (!is.character(path) || length(path) != 1L || is.na(path)) {
    stop("path must be a single string")
  }
  info <- file.info(path)
  if (is.na(info$size) || info$isdir) {
    stop("path must reference a readable file")
  }
  data <- readBin(path, "raw", n = info$size)
  image_data_hash_raw(data, algorithm)
}
