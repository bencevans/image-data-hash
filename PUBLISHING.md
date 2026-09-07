# Publishing Image Data Hash

Repository: https://github.com/bencevans/image-data-hash

Maintainer: Ben Evans <Benjamin.Evans@ioz.ac.uk>. All implementations use MIT.
No command in the test workflow publishes packages. Publishing requires the
maintainer's registry accounts and explicit execution of the release commands.

## Before release

1. Complete the GitHub repository rename to `bencevans/image-data-hash` and update
   the local Git remote. The metadata and documentation already use that URL.
2. Keep the versions in the npm, Python, Rust and R manifests aligned. Composer
   derives release versions from Git tags; do not add a static version field.
3. Generate fixtures and run every suite as described in the implementation READMEs.
4. Run the build and validation commands below and inspect archive contents.
   Ensure wheels include `py.typed`, npm includes `dist/index.d.ts`, and all
   packages contain the MIT license.
5. Commit the release, wait for CI, then create the matching `v0.1.0` tag.

## npm

From `image-data-hash-js`:

```sh
npm ci
npm test
npm pack --dry-run
# After reviewing the release:
npm publish --access public
```

The prepack script compiles TypeScript. Only built files, TypeScript source,
README and LICENSE are included. JavaScript users do not need TypeScript installed.

## PyPI

From `image-data-hash-py`:

```sh
uv run pytest -q
uv build
uvx twine check dist/*
# After reviewing the release:
uv publish
```

The distribution and import name is `image_data_hash`.

## crates.io

From `image-data-hash-rs`, with a clean committed working tree:

The Cargo package and crate name is `image_data_hash`.

```sh
cargo test --locked
cargo fmt --check
cargo doc --no-deps
cargo package
# After reviewing the release:
cargo publish
```

The crate's release archive excludes repository-only compatibility tests and
camera fixtures. Those tests run in CI before publication.

## R (GitHub releases)

R is distributed through tagged GitHub releases, not CRAN. After pushing the
release tag, users can install it with:

```r
remotes::install_github("bencevans/image-data-hash", subdir = "image-data-hash-r", ref = "v0.1.0")
```

Install `remotes` first with `install.packages("remotes")` if needed.
Keep the tag in the R README aligned with the intended release.

### Optional future CRAN submission

From the repository root:

```sh
R CMD build image-data-hash-r
R CMD check --as-cran imageDataHash_0.1.0.tar.gz
```

If CRAN distribution is chosen later, submit the checked source archive through
CRAN's submission form. CRAN review,
email confirmation and registry acceptance are separate from local checks.
The R package is named `imageDataHash`.

## Packagist

Validate both the distribution manifest and the PHP development manifest:

```sh
composer validate --strict
composer --working-dir=image-data-hash-php validate --strict
composer --working-dir=image-data-hash-php test
```

Submit `https://github.com/bencevans/image-data-hash` to Packagist and configure
its GitHub update hook. The root `composer.json` makes the monorepo directly
installable as `bencevans/image-data-hash`; it autoloads the PHP implementation.
The nested manifest is for standalone PHP development and formatter dependencies.
GitHub-generated distribution archives contain the monorepo; Composer's own
archive command applies the root manifest's exclusions.

Consumers receive releases from Git tags, such as `v0.1.0`. Registry submission,
tag creation and publication are not performed by the build/test commands above.
