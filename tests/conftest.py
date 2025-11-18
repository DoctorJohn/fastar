import sys
from pathlib import Path
from typing import Literal, Tuple

import pytest
from typing_extensions import TypeAlias

import fastar

WriteMode: TypeAlias = Literal["w", "w:gz", "w:zst"]
ReadMode: TypeAlias = Literal["r", "r:gz", "r:zst"]


@pytest.fixture
def archive_path(tmp_path) -> Path:
    return tmp_path / "archive.tar.gz"


@pytest.fixture
def source_path(tmp_path) -> Path:
    path = tmp_path / "source"
    path.mkdir()
    return path


@pytest.fixture
def target_path(tmp_path) -> Path:
    path = tmp_path / "target"
    path.mkdir()
    return path


@pytest.fixture(
    params=[
        pytest.param(("w", "r"), id="uncompressed"),
        pytest.param(("w:gz", "r:gz"), id="gzip_compressed"),
        pytest.param(
            ("w:zst", "r:zst"),
            marks=pytest.mark.skipif(
                sys.version_info < (3, 14),
                reason="Before 3.14, tarfile did not support zstd compression",
            ),
            id="zstd_compressed",
        ),
    ]
)
def modes(request) -> Tuple[WriteMode, ReadMode]:
    return request.param


@pytest.fixture
def write_mode(modes) -> WriteMode:
    return modes[0]


@pytest.fixture
def read_mode(modes) -> ReadMode:
    return modes[1]


@pytest.fixture
def large_source_path(tmp_path):
    source = tmp_path / "large_source"
    source.mkdir()

    for i in range(1000):
        file_path = source / f"file_{i:04d}.txt"
        file_path.write_text(f"Content for file {i}\n" * 50)

    return source


@pytest.fixture
def large_archive_path(archive_path, write_mode, large_source_path):
    with fastar.open(archive_path, write_mode) as archive:
        archive.append(large_source_path)

    return archive_path
