import tarfile

import pytest

import fastar


def test_open_raises_on_unsupported_mode(archive_path):
    with pytest.raises(
        ValueError,
        match="unsupported mode; supported modes are 'w', 'w:gz', 'w:zst', 'r', 'r:gz', 'r:zst'",
    ):
        fastar.open(archive_path, "invalid-mode")  # type: ignore[call-overload]


@pytest.mark.parametrize(
    ("open_mode", "expected_class"),
    [
        ("w", fastar.ArchiveWriter),
        ("w:gz", fastar.ArchiveWriter),
    ],
)
def test_open_returns_expected_archive_writer(archive_path, open_mode, expected_class):
    with fastar.open(archive_path, open_mode) as archive:
        assert isinstance(archive, expected_class)


@pytest.mark.parametrize(
    ("create_mode", "open_mode", "expected_class"),
    [
        ("w", "r", fastar.ArchiveReader),
        ("w:gz", "r:gz", fastar.ArchiveReader),
    ],
)
def test_open_returns_expected_archive_reader(
    archive_path, create_mode, open_mode, expected_class
):
    with tarfile.open(archive_path, create_mode):
        pass

    with fastar.open(archive_path, open_mode) as archive:
        assert isinstance(archive, expected_class)
