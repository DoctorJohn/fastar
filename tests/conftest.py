from typing import Literal, TypeAlias
from pathlib import Path
import pytest


WriteMode: TypeAlias = Literal["w", "w:gz"]
ReadMode: TypeAlias = Literal["r", "r:gz"]


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


@pytest.fixture(params=[("w", "r"), ("w:gz", "r:gz")])
def modes(request) -> tuple[WriteMode, ReadMode]:
    return request.param


@pytest.fixture
def write_mode(modes) -> WriteMode:
    return modes[0]


@pytest.fixture
def read_mode(modes) -> ReadMode:
    return modes[1]
