# Fastar

[![Versions][versions-image]][versions-url]
[![PyPI][pypi-image]][pypi-url]
[![Downloads][downloads-image]][downloads-url]
[![License][license-image]][license-url]
[![CodSpeed][codspeed-image]][codspeed-url]

[versions-image]: https://img.shields.io/pypi/pyversions/fastar
[versions-url]: https://github.com/DoctorJohn/fastar/blob/main/pyproject.toml
[pypi-image]: https://img.shields.io/pypi/v/fastar
[pypi-url]: https://pypi.org/project/fastar/
[downloads-image]: https://img.shields.io/pypi/dm/fastar
[downloads-url]: https://pypi.org/project/fastar/
[license-image]: https://img.shields.io/pypi/l/fastar
[license-url]: https://github.com/DoctorJohn/fastar/blob/main/LICENSE
[codspeed-image]: https://img.shields.io/endpoint?url=https://codspeed.io/badge.json
[codspeed-url]: https://codspeed.io/DoctorJohn/fastar

The `fastar` library wraps the Rust [tar](https://crates.io/crates/tar), [flate2](https://crates.io/crates/flate2), and [zstd](https://crates.io/crates/zstd) crates, providing a high-performance way to work with compressed and uncompressed tar archives in Python.

## Installation

```sh
pip install fastar
```

## Usage

This section shows basic examples of how to create and extract tar archives using Fastar. For more usage examples, please refer directly to the test cases in the [tests](https://github.com/DoctorJohn/fastar/tree/main/tests) directory.

### Working with uncompressed tar archives

```python
import fastar
from pathlib import Path


input_file = Path("file.txt")
input_file.write_text("Hello, Fastar!")


with fastar.open("archive.tar", "w") as archive:
    archive.append(input_file)


with fastar.open("archive.tar", "r") as archive:
    archive.unpack("output/")


unpacked_file = Path("output/file.txt")
print(unpacked_file.read_text())  # Hello, Fastar!
```

### Working with gzip-compressed tar archives

```python
import fastar
from pathlib import Path


input_file = Path("file.txt")
input_file.write_text("Hello, Fastar!")


with fastar.open("archive.tar.gz", "w:gz") as archive:
    archive.append(input_file)


with fastar.open("archive.tar.gz", "r:gz") as archive:
    archive.unpack("output/")


unpacked_file = Path("output/file.txt")
print(unpacked_file.read_text())  # Hello, Fastar!
```

### Working with zstd-compressed tar archives

```python
import fastar
from pathlib import Path


input_file = Path("file.txt")
input_file.write_text("Hello, Fastar!")


with fastar.open("archive.tar.zst", "w:zst") as archive:
    archive.append(input_file)


with fastar.open("archive.tar.zst", "r:zst") as archive:
    archive.unpack("output/")


unpacked_file = Path("output/file.txt")
print(unpacked_file.read_text())  # Hello, Fastar!
```

## Development

1. Install dependencies into a virtual env: `uv sync`
2. Make changes to the code and tests
3. Build the package: `uv run maturin develop`
4. Run the tests: `uv run pytest`
