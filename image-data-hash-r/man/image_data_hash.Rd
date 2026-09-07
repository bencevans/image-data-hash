\name{image_data_hash}
\alias{image_data_hash}
\alias{image_data_hash_raw}
\title{Hash JPEG Image Data Using ExifTool-Compatible Rules}
\description{Computes MD5, SHA-256 or SHA-512 over JPEG scan chunks. Metadata
before the scans is excluded. No external executable is needed.}
\usage{
image_data_hash(path, algorithm = "md5")
image_data_hash_raw(data, algorithm = "md5")
}
\arguments{
  \item{path}{Path to a JPEG file.}
  \item{data}{A raw vector containing JPEG bytes.}
  \item{algorithm}{One of md5, sha256 or sha512. Case and hyphens are ignored.}
}
\value{A lowercase hexadecimal hash string of 32 (MD5), 64 (SHA-256),
or 128 (SHA-512) characters.}
\details{The implementation reads the JPEG into memory. It follows ExifTool's
ImageDataHash scan-chunk selection rather than hashing decoded pixels.
Unsupported algorithms and malformed or truncated JPEG input raise an error.}
