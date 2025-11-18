import hashlib
import os
import sys
import tarfile
from datetime import datetime
from random import randint

import psutil
import pytest

from fastar import ArchiveClosedError, ArchiveReader, ArchiveUnpackingError


def test_open_raises_on_unsupported_mode(archive_path):
    with pytest.raises(
        ValueError,
        match="unsupported mode; only 'r', 'r:gz', and 'r:zst' are supported",
    ):
        ArchiveReader.open(archive_path, "invalid-mode")  # type: ignore[arg-type]


def test_open_raises_if_file_does_not_exist(archive_path, read_mode):
    if archive_path.exists():
        archive_path.unlink()

    with pytest.raises(
        FileNotFoundError,
        match="No such file or directory",
    ):
        ArchiveReader.open(archive_path, read_mode)


@pytest.mark.xfail(
    reason="""
        Not fully supported in Rust yet
        https://github.com/rust-lang/rust/issues/71213
        https://doc.rust-lang.org/beta/std/os/wasi/fs/trait.OpenOptionsExt.html#tymethod.directory
    """
)
def test_open_raises_if_path_is_directory(tmp_path, read_mode):
    with pytest.raises(
        IsADirectoryError,
        match="is a directory, not an archive file",
    ):
        ArchiveReader.open(tmp_path, read_mode)


def test_open_raises_if_insufficient_permissions(archive_path, read_mode):
    archive_path.touch()
    archive_path.chmod(0o000)

    with pytest.raises(
        PermissionError,
        match="Permission denied",
    ):
        ArchiveReader.open(archive_path, read_mode)


def test_close_closes_archive(archive_path, write_mode, read_mode):
    with tarfile.open(archive_path, write_mode):
        pass

    process = psutil.Process()
    assert process.open_files() == []

    archive = ArchiveReader.open(archive_path, read_mode)

    open_files = process.open_files()
    assert len(open_files) == 1
    assert open_files[0].path == str(archive_path)

    archive.close()
    assert process.open_files() == []


def test_context_manager_closes_archive(archive_path, write_mode, read_mode):
    with tarfile.open(archive_path, write_mode):
        pass

    process = psutil.Process()
    assert process.open_files() == []

    with ArchiveReader.open(archive_path, read_mode):
        open_files = process.open_files()
        assert len(open_files) == 1
        assert open_files[0].path == str(archive_path)

    assert process.open_files() == []


def test_unpack_raises_if_archive_is_already_closed(
    archive_path, write_mode, read_mode
):
    with tarfile.open(archive_path, write_mode):
        pass

    reader = ArchiveReader.open(archive_path, read_mode)
    reader.close()

    with pytest.raises(ArchiveClosedError, match="archive is already closed"):
        reader.unpack("some/path")


def test_unpack_unpacks_files(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_file = source_path / "file.txt"
    input_file.touch()

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname="file.txt")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_file = target_path / "file.txt"
    assert output_file.exists()
    assert output_file.is_file()


def test_unpack_unpacks_directories(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_dir = source_path / "dir"
    input_dir.mkdir()

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_dir, arcname="dir/")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_dir = target_path / "dir"
    assert output_dir.exists()
    assert output_dir.is_dir()


def test_unpack_unpacks_nested_files(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_file = source_path / "file.txt"
    input_file.touch()

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname="deeply/nested/file.txt")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_nested_file = target_path / "deeply" / "nested" / "file.txt"
    assert output_nested_file.exists()
    assert output_nested_file.is_file()


def test_unpack_unpacks_nested_directories(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_dir = source_path / "dir"
    input_dir.mkdir()

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_dir, arcname="deeply/nested/dir/")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_nested_dir = target_path / "deeply" / "nested" / "dir"
    assert output_nested_dir.exists()
    assert output_nested_dir.is_dir()


def test_unpack_unpacks_all_contents(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_file = source_path / "file.txt"
    input_file.touch()

    input_dir = source_path / "dir"
    input_dir.mkdir()

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_dir, arcname="dir1")
        archive.add(input_file, arcname="file1.txt")
        archive.add(input_file, arcname="dir1/file2.txt")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_dir1 = target_path / "dir1"
    assert output_dir1.exists()
    assert output_dir1.is_dir()

    output_file1 = target_path / "file1.txt"
    assert output_file1.exists()
    assert output_file1.is_file()

    output_file2 = output_dir1 / "file2.txt"
    assert output_file2.exists()
    assert output_file2.is_file()


def test_unpack_preserves_file_contents(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_file = source_path / "file.txt"
    input_file.write_text("Test content")

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname="file.txt")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_file = target_path / "file.txt"
    assert output_file.read_text() == "Test content"


@pytest.mark.parametrize("permissions", [0o644, 0o600, 0o755, 0o700])
def test_unpack_preserves_file_permissions(
    source_path, target_path, archive_path, write_mode, read_mode, permissions
):
    input_file = source_path / "file.txt"
    input_file.touch()
    input_file.chmod(permissions)

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname="file.txt")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_file = target_path / "file.txt"
    assert output_file.stat().st_mode & 0o777 == permissions


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="Before 3.9, tarfile perserved mtime in a non-compatible way",
)
def test_unpack_preserves_file_modification_time_by_default(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_file = source_path / "file.txt"
    input_file.touch()

    timestamp = randint(1_600_000_000, 1_700_000_000)
    os.utime(input_file, (timestamp, timestamp))

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname="file.txt")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_file = target_path / "file.txt"
    assert output_file.stat().st_mtime == timestamp


@pytest.mark.skipif(
    sys.version_info < (3, 9),
    reason="Before 3.9, tarfile perserved mtime in a non-compatible way",
)
@pytest.mark.parametrize("preserve", [True, False])
def test_unpack_preserves_file_modification_time_only_if_option_is_true(
    source_path, target_path, archive_path, write_mode, read_mode, preserve
):
    input_file = source_path / "file.txt"
    input_file.touch()

    timestamp = randint(1_600_000_000, 1_700_000_000)
    os.utime(input_file, (timestamp, timestamp))

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname="file.txt")

    archive_open_time = datetime.now().timestamp()

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path, preserve_mtime=preserve)

    output_file = target_path / "file.txt"
    assert (output_file.stat().st_mtime == timestamp) == preserve
    assert (output_file.stat().st_mtime >= archive_open_time) == (not preserve)


@pytest.mark.parametrize("permissions", [0o755, 0o700, 0o775, 0o777])
def test_unpack_preserves_directory_permissions(
    source_path, target_path, archive_path, write_mode, read_mode, permissions
):
    input_dir = source_path / "dir"
    input_dir.mkdir()
    input_dir.chmod(permissions)

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_dir, arcname="dir/")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_dir = target_path / "dir"
    assert output_dir.stat().st_mode & 0o777 == permissions


@pytest.mark.parametrize("dir_name", ["dir", "dir/"])
def test_unpack_handles_trailing_slash_in_directory_name(
    source_path, target_path, archive_path, write_mode, read_mode, dir_name
):
    input_dir = source_path / dir_name
    input_dir.mkdir()

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_dir, arcname=dir_name)

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_dir = target_path / "dir"
    assert output_dir.exists()
    assert output_dir.is_dir()


def test_unpack_overwrites_contents_of_conflicting_files(
    source_path, target_path, archive_path, write_mode, read_mode
):
    existing_file = target_path / "file.txt"
    existing_file.write_text("Old content")

    input_file = source_path / "file.txt"
    input_file.write_text("New content")

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname="file.txt")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_file = target_path / "file.txt"
    assert output_file.read_text() == "New content"


def test_unpack_overwrites_permissions_of_conflicting_files(
    source_path, target_path, archive_path, write_mode, read_mode
):
    existing_file = target_path / "file.txt"
    existing_file.touch()
    os.chmod(existing_file, 0o700)

    input_file = source_path / "file.txt"
    input_file.touch()
    os.chmod(input_file, 0o755)

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname="file.txt")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_file = target_path / "file.txt"
    assert output_file.exists()
    assert output_file.is_file()
    assert output_file.stat().st_mode & 0o777 == 0o755


def test_unpack_overwrites_permissions_of_conflicting_directories(
    source_path, target_path, archive_path, write_mode, read_mode
):
    existing_dir = target_path / "dir"
    existing_dir.mkdir()
    os.chmod(existing_dir, 0o700)

    input_dir = source_path / "dir"
    input_dir.mkdir()
    os.chmod(input_dir, 0o755)

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_dir, arcname="dir/")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_dir = target_path / "dir"
    assert output_dir.exists()
    assert output_dir.is_dir()
    assert output_dir.stat().st_mode & 0o777 == 0o755


def test_unpack_keeps_contents_of_conflicting_directories(
    source_path, target_path, archive_path, write_mode, read_mode
):
    existing_dir = target_path / "dir"
    existing_dir.mkdir()
    os.chmod(existing_dir, 0o700)

    existing_file = existing_dir / "existing_file.txt"
    existing_file.write_text("Existing content")

    input_dir = source_path / existing_dir.name
    input_dir.mkdir()
    os.chmod(input_dir, 0o755)

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_dir, arcname=existing_dir.name)

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_dir = target_path / "dir"
    assert output_dir.exists()
    assert output_dir.is_dir()
    assert output_dir.stat().st_mode & 0o777 == 0o755

    output_existing_file = output_dir / "existing_file.txt"
    assert output_existing_file.exists()
    assert output_existing_file.is_file()
    assert output_existing_file.read_text() == "Existing content"


def test_unpack_raises_if_file_would_overwrite_existing_directory(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_file = source_path / "conflict"
    input_file.touch()

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname="conflict")

    conflict_path = target_path / "conflict"
    conflict_path.mkdir()

    with ArchiveReader.open(archive_path, read_mode) as reader:
        with pytest.raises(IsADirectoryError, match="failed to unpack"):
            reader.unpack(target_path)


def test_unpack_raises_if_directory_would_overwrite_existing_file(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_dir = source_path / "conflict"
    input_dir.mkdir()

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_dir, arcname="conflict/")

    conflict_path = target_path / "conflict"
    conflict_path.touch()

    with ArchiveReader.open(archive_path, read_mode) as reader:
        with pytest.raises(FileExistsError, match="failed to unpack"):
            reader.unpack(target_path)


def test_unpack_unpacks_absolute_paths_relative_to_the_target_dir(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_file = source_path / "file.txt"
    input_file.touch()

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname="/absolute/path/file.txt")

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    output_file = target_path / "absolute" / "path" / "file.txt"
    assert output_file.exists()
    assert output_file.is_file()


@pytest.mark.parametrize("arcname", ["../outside.txt", "parent/../inside.txt"])
def test_unpack_ignores_relative_paths_outside_the_target_dir(
    source_path, target_path, archive_path, write_mode, read_mode, arcname
):
    input_file = source_path / "file.txt"
    input_file.touch()

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname=arcname)

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path / "nested")

    assert list(target_path.glob("**/*.txt")) == []


def test_unpack_creates_target_directory_if_it_does_not_exist(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_file = source_path / "file.txt"
    input_file.touch()

    nested_target_path = target_path / "nested" / "dir"
    assert not nested_target_path.exists()

    with tarfile.open(archive_path, write_mode):
        pass

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(nested_target_path)

    assert nested_target_path.exists()
    assert nested_target_path.is_dir()


def test_unpack_does_nothing_on_empty_archive(
    target_path, archive_path, write_mode, read_mode
):
    with tarfile.open(archive_path, write_mode):
        pass

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    assert not any(target_path.iterdir())


def test_unpack_does_not_alter_archive(
    source_path, target_path, archive_path, write_mode, read_mode
):
    input_file = source_path / "file.txt"
    input_file.touch()

    with tarfile.open(archive_path, write_mode) as archive:
        archive.add(input_file, arcname="file.txt")

    archive_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()

    with ArchiveReader.open(archive_path, read_mode) as reader:
        reader.unpack(target_path)

    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == archive_hash


def test_unpack_raises_when_archive_entries_are_not_iterable(target_path, archive_path):
    with tarfile.open(archive_path, "w:gz"):
        pass

    with ArchiveReader.open(archive_path, "r") as reader:
        with pytest.raises(
            ArchiveUnpackingError, match="failed to iterate over archive"
        ):
            reader.unpack(target_path)
