# Fastar

[![Versions][versions-image]][versions-url]
[![PyPI][pypi-image]][pypi-url]
[![Downloads][downloads-image]][downloads-url]
[![License][license-image]][license-url]

[versions-image]: https://img.shields.io/pypi/pyversions/fastar
[versions-url]: https://github.com/DoctorJohn/fastar/blob/main/pyproject.toml
[pypi-image]: https://img.shields.io/pypi/v/fastar
[pypi-url]: https://pypi.org/project/fastar/
[downloads-image]: https://img.shields.io/pypi/dm/fastar
[downloads-url]: https://pypi.org/project/fastar/
[license-image]: https://img.shields.io/pypi/l/fastar
[license-url]: https://github.com/DoctorJohn/fastar/blob/main/LICENSE

High-level bindings for the Rust [tar](https://crates.io/crates/tar) crate.

## Installation

```sh
pip install fastar
```

## Usage

```python
import fastar
from pathlib import Path


some_file = Path('file.txt')
some_file.write_text('Hello, Fastar!')


with fastar.open('archive.tar', 'w') as archive:
    archive.add(some_file)


with fastar.open('archive.tar', 'r') as archive:
    archive.extract(Path("extracted/"))


extracted_file = Path('extracted/file.txt')
print(extracted_file.read_text())  # Hello, Fastar!
```

## Development

1. Install dependencies into a virtual env: `uv sync`
2. Make changes to the code and tests
3. Build the package: `uv run maturin develop`
4. Run the tests: `uv run pytest`
