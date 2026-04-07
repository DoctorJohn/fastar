import sys

import pytest

import fastar

if sys.version_info >= (3, 9) and sys.version_info < (3, 14):
    from backports.zstd import tarfile
else:
    import tarfile


def test_open_raises_on_unsupported_mode(archive_path):
    with pytest.raises(
        ValueError,
        match="unsupported mode; supported modes are 'w', 'w:gz', 'w:zst', 'r', 'r:', 'r:gz', 'r:zst'",
    ):
        fastar.open(archive_path, "invalid-mode")  # type: ignore[call-overload]


@pytest.mark.parametrize(
    ("open_mode", "expected_class"),
    [
        ("w", fastar.ArchiveWriter),
        ("w:gz", fastar.ArchiveWriter),
        ("w:zst", fastar.ArchiveWriter),
    ],
)
def test_open_returns_expected_archive_writer(archive_path, open_mode, expected_class):
    with fastar.open(archive_path, open_mode) as archive:
        assert isinstance(archive, expected_class)


@pytest.mark.parametrize(
    ("create_mode", "open_mode", "expected_class"),
    [
        ("w", "r", fastar.ArchiveReader),
        ("w", "r:", fastar.ArchiveReader),
        ("w:gz", "r:gz", fastar.ArchiveReader),
        ("w:zst", "r:zst", fastar.ArchiveReader),
    ],
)
def test_open_returns_expected_archive_reader(
    archive_path, create_mode, open_mode, expected_class
):
    with fastar.open(archive_path, create_mode):
        pass

    with fastar.open(archive_path, open_mode) as archive:
        assert isinstance(archive, expected_class)


def test_open_and_append_with_sparse_option_disabled(
    source_path, archive_path, write_mode, read_mode
):
    file_path = source_path / "file.txt"
    file_path.touch()

    with fastar.open(archive_path, write_mode, sparse=False) as writer:
        writer.append(file_path)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["file.txt"]
        assert archive.getmember("file.txt").isfile()
