import pytest
import fastar


def test_open_raises_on_unsupported_mode(archive_path):
    with pytest.raises(
        RuntimeError, match="unsupported mode; supported modes are 'w', 'w:gz'"
    ):
        fastar.open(archive_path, "invalid-mode")


def test_open_returns_archive_writer_instance(archive_path):
    with fastar.open(archive_path, "w") as archive:
        assert isinstance(archive, fastar.ArchiveWriter)
