# In-memory implementation of jpeg_content_sha256_v1.
# Retained byte ranges are assembled once; scan searches run in vectorized R.

.canonical_jpeg <- function(data) {
  n <- length(data)
  if (n < 4 || !identical(data[1:2], as.raw(c(255, 216)))) stop("not a JPEG file")
  marker_offsets <- which(data == as.raw(255))
  chunks <- list(data[1:2])
  add <- function(from, to) if (to >= from) chunks[[length(chunks) + 1]] <<- data[from:to]
  pos <- 3; in_scan <- FALSE; scan_start <- 0
  while (pos <= n) {
    if (in_scan) {
      next_marker <- findInterval(pos - 1, marker_offsets) + 1L
      if (next_marker > length(marker_offsets)) stop("JPEG has no EOI marker")
      pos <- marker_offsets[next_marker]
    }
    marker_start <- pos
    if (data[pos] != as.raw(255)) stop(sprintf("unexpected data at offset %d", pos - 1))
    while (pos <= n && data[pos] == as.raw(255)) pos <- pos + 1
    if (pos > n) stop("truncated JPEG marker")
    marker <- as.integer(data[pos]); pos <- pos + 1
    if (in_scan && (marker == 0L || (marker >= 208L && marker <= 215L))) next
    if (in_scan) { add(scan_start, marker_start - 1); in_scan <- FALSE }
    if (marker == 217L) {
      add(marker_start, pos - 1)
      return(do.call(c, chunks))
    }
    if (marker == 1L || (marker >= 208L && marker <= 216L)) {
      add(marker_start, pos - 1); next
    }
    if (pos + 1 > n) stop("truncated JPEG segment length")
    len <- as.integer(data[pos]) * 256L + as.integer(data[pos + 1])
    if (len < 2L || pos + len - 1 > n) stop("invalid or truncated JPEG segment")
    end <- pos + len - 1
    if (!(marker %in% c(225L, 237L, 254L))) add(marker_start, end)
    pos <- end + 1
    in_scan <- marker == 218L
    if (in_scan) scan_start <- pos
  }
  stop("JPEG has no EOI marker")
}

jpeg_content_sha256_raw <- function(data) {
  if (!is.raw(data)) stop("data must be a raw vector")
  digest::digest(.canonical_jpeg(data), algo = "sha256", serialize = FALSE)
}

jpeg_content_sha256 <- function(path) {
  if (!is.character(path) || length(path) != 1L || is.na(path)) stop("path must be a single string")
  size <- file.info(path)$size
  if (is.na(size) || file.info(path)$isdir) stop("path must reference a readable file")
  jpeg_content_sha256_raw(readBin(path, what = "raw", n = size))
}
