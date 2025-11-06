import tarfile
from fastar import ArchiveWriter
import pytest
import psutil


def test_open_raises_on_unsupported_mode(archive_path):
    with pytest.raises(
        RuntimeError, match="unsupported mode; only 'w' and 'w:gz' are supported"
    ):
        ArchiveWriter.open(archive_path, "invalid-mode")  # type: ignore[arg-type]


def test_opening_and_closing_creates_empty_archive(archive_path, write_mode, read_mode):
    archive = ArchiveWriter.open(archive_path, write_mode)
    archive.close()

    with tarfile.open(archive_path, read_mode) as tarfile_archive:
        assert tarfile_archive.getnames() == []


def test_context_manager_created_empty_archive(archive_path, write_mode, read_mode):
    with ArchiveWriter.open(archive_path, write_mode):
        pass

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == []


def test_close_closes_archive(archive_path, write_mode):
    archive = ArchiveWriter.open(archive_path, write_mode)

    process = psutil.Process()
    open_files = process.open_files()
    assert len(open_files) == 1
    assert open_files[0].path == str(archive_path)

    archive.close()
    assert process.open_files() == []


def test_context_manager_closes_archive(archive_path, write_mode):
    process = psutil.Process()

    with ArchiveWriter.open(archive_path, write_mode):
        open_files = process.open_files()
        assert len(open_files) == 1
        assert open_files[0].path == str(archive_path)

    assert process.open_files() == []


def test_add_raises_if_archive_is_already_closed(tmp_path, archive_path, write_mode):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    archive = ArchiveWriter.open(archive_path, write_mode)
    archive.close()

    with pytest.raises(RuntimeError, match="archive is already closed"):
        archive.add(file_path)


def test_add_raises_if_file_name_cannot_be_determined(
    tmp_path, archive_path, write_mode
):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        with pytest.raises(RuntimeError, match="cannot derive name from path"):
            archive.add(file_path / "..")


def test_add_raises_if_path_does_not_exist(tmp_path, archive_path, write_mode):
    non_existing_path = tmp_path / "non_existing.txt"

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        with pytest.raises(RuntimeError, match="path does not exist"):
            archive.add(non_existing_path)


def test_adding_a_single_file(tmp_path, archive_path, write_mode, read_mode):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["file.txt"]
        assert archive.getmember("file.txt").isfile()


def test_adding_multiple_files(tmp_path, archive_path, write_mode, read_mode):
    file_path1 = tmp_path / "file1.txt"
    file_path1.touch()

    file_path2 = tmp_path / "file2.txt"
    file_path2.touch()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path1)
        archive.add(file_path2)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["file1.txt", "file2.txt"]
        assert archive.getmember("file1.txt").isfile()
        assert archive.getmember("file2.txt").isfile()


def test_adding_a_single_director(tmp_path, archive_path, write_mode, read_mode):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["dir"]
        assert archive.getmember("dir").isdir()


def test_adding_multiple_directorie(tmp_path, archive_path, write_mode, read_mode):
    dir_path1 = tmp_path / "dir1"
    dir_path1.mkdir()

    dir_path2 = tmp_path / "dir2"
    dir_path2.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path1)
        archive.add(dir_path2)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["dir1", "dir2"]
        assert archive.getmember("dir1").isdir()
        assert archive.getmember("dir2").isdir()


def test_adding_a_single_nested_file(tmp_path, archive_path, write_mode, read_mode):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path, arcname="nested/file.txt")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["nested/file.txt"]
        assert archive.getmember("nested/file.txt").isfile()


def test_adding_multiple_nested_files(tmp_path, archive_path, write_mode, read_mode):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path, arcname="nested/file1.txt")
        archive.add(file_path, arcname="nested/file2.txt")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["nested/file1.txt", "nested/file2.txt"]
        assert archive.getmember("nested/file1.txt").isfile()
        assert archive.getmember("nested/file2.txt").isfile()


def test_adding_a_single_nested_directory(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, arcname="nested/dir")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["nested/dir"]
        assert archive.getmember("nested/dir").isdir()


def test_adding_multiple_nested_directories(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, arcname="nested/dir1")
        archive.add(dir_path, arcname="nested/dir2")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["nested/dir1", "nested/dir2"]
        assert archive.getmember("nested/dir1").isdir()
        assert archive.getmember("nested/dir2").isdir()


def test_adding_a_single_deeply_nested_file(
    tmp_path, archive_path, write_mode, read_mode
):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path, arcname="super/duper/deeply/nested/file.txt")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["super/duper/deeply/nested/file.txt"]
        assert archive.getmember("super/duper/deeply/nested/file.txt").isfile()


def test_adding_multiple_deeply_nested_files(
    tmp_path, archive_path, write_mode, read_mode
):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path, arcname="super/duper/deeply/nested/file1.txt")
        archive.add(file_path, arcname="super/duper/deeply/nested/file2.txt")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == [
            "super/duper/deeply/nested/file1.txt",
            "super/duper/deeply/nested/file2.txt",
        ]
        assert archive.getmember("super/duper/deeply/nested/file1.txt").isfile()
        assert archive.getmember("super/duper/deeply/nested/file2.txt").isfile()


def test_adding_a_single_deeply_nested_directory(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, arcname="super/duper/deeply/nested/dir")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["super/duper/deeply/nested/dir"]
        assert archive.getmember("super/duper/deeply/nested/dir").isdir()


def test_adding_multiple_deeply_nested_directories(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, arcname="super/duper/deeply/nested/dir1")
        archive.add(dir_path, arcname="super/duper/deeply/nested/dir2")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == [
            "super/duper/deeply/nested/dir1",
            "super/duper/deeply/nested/dir2",
        ]
        assert archive.getmember("super/duper/deeply/nested/dir1").isdir()
        assert archive.getmember("super/duper/deeply/nested/dir2").isdir()


def test_adding_files_and_directories(tmp_path, archive_path, write_mode, read_mode):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path)
        archive.add(dir_path)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["file.txt", "dir"]
        assert archive.getmember("file.txt").isfile()
        assert archive.getmember("dir").isdir()


def test_adding_nested_files_and_directories(
    tmp_path, archive_path, write_mode, read_mode
):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path, arcname="nested/file.txt")
        archive.add(dir_path, arcname="nested/dir")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["nested/file.txt", "nested/dir"]
        assert archive.getmember("nested/file.txt").isfile()
        assert archive.getmember("nested/dir").isdir()


def test_adding_deeply_nested_files_and_directories(
    tmp_path, archive_path, write_mode, read_mode
):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path, arcname="super/duper/deeply/nested/file.txt")
        archive.add(dir_path, arcname="super/duper/deeply/nested/dir")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == [
            "super/duper/deeply/nested/file.txt",
            "super/duper/deeply/nested/dir",
        ]
        assert archive.getmember("super/duper/deeply/nested/file.txt").isfile()
        assert archive.getmember("super/duper/deeply/nested/dir").isdir()


def test_adding_multi_level_files(tmp_path, archive_path, write_mode, read_mode):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path)
        archive.add(file_path, arcname="nested/file.txt")
        archive.add(file_path, arcname="super/duper/deeply/nested/file.txt")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == [
            "file.txt",
            "nested/file.txt",
            "super/duper/deeply/nested/file.txt",
        ]
        assert archive.getmember("file.txt").isfile()
        assert archive.getmember("nested/file.txt").isfile()
        assert archive.getmember("super/duper/deeply/nested/file.txt").isfile()


def test_adding_multi_level_directories(tmp_path, archive_path, write_mode, read_mode):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path)
        archive.add(dir_path, arcname="nested/dir")
        archive.add(dir_path, arcname="super/duper/deeply/nested/dir")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == [
            "dir",
            "nested/dir",
            "super/duper/deeply/nested/dir",
        ]
        assert archive.getmember("dir").isdir()
        assert archive.getmember("nested/dir").isdir()
        assert archive.getmember("super/duper/deeply/nested/dir").isdir()


def test_adding_multi_level_files_and_directories(
    tmp_path, archive_path, write_mode, read_mode
):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path)
        archive.add(file_path, arcname="nested/file.txt")
        archive.add(file_path, arcname="super/duper/deeply/nested/file.txt")

        archive.add(dir_path)
        archive.add(dir_path, arcname="nested/dir")
        archive.add(dir_path, arcname="super/duper/deeply/nested/dir")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == [
            "file.txt",
            "nested/file.txt",
            "super/duper/deeply/nested/file.txt",
            "dir",
            "nested/dir",
            "super/duper/deeply/nested/dir",
        ]

        assert archive.getmember("file.txt").isfile()
        assert archive.getmember("nested/file.txt").isfile()
        assert archive.getmember("super/duper/deeply/nested/file.txt").isfile()

        assert archive.getmember("dir").isdir()
        assert archive.getmember("nested/dir").isdir()
        assert archive.getmember("super/duper/deeply/nested/dir").isdir()


def test_adding_directory_with_items_recursively(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "parent"
    dir_path.mkdir()

    item_file_path = dir_path / "file.txt"
    item_file_path.touch()

    item_dir_path = dir_path / "dir"
    item_dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, recursive=True)

    with tarfile.open(archive_path, read_mode) as archive:
        assert set(archive.getnames()) == {"parent", "parent/dir", "parent/file.txt"}
        assert archive.getmember("parent").isdir()
        assert archive.getmember("parent/dir").isdir()
        assert archive.getmember("parent/file.txt").isfile()


def test_adding_directory_with_nested_items_recursively(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "parent"
    dir_path.mkdir()

    nested_dir_path = dir_path / "nested"
    nested_dir_path.mkdir()

    item_file_path = nested_dir_path / "file.txt"
    item_file_path.touch()

    item_dir_path = nested_dir_path / "dir"
    item_dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, recursive=True)

    with tarfile.open(archive_path, read_mode) as archive:
        assert set(archive.getnames()) == {
            "parent",
            "parent/nested",
            "parent/nested/dir",
            "parent/nested/file.txt",
        }
        assert archive.getmember("parent").isdir()
        assert archive.getmember("parent/nested").isdir()
        assert archive.getmember("parent/nested/dir").isdir()
        assert archive.getmember("parent/nested/file.txt").isfile()


def test_adding_directory_with_deeply_nested_items_recursively(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "parent"
    dir_path.mkdir()

    nested_dir_path = dir_path / "super" / "duper" / "deeply" / "nested"
    nested_dir_path.mkdir(parents=True)

    item_file_path = nested_dir_path / "file.txt"
    item_file_path.touch()

    item_dir_path = nested_dir_path / "dir"
    item_dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, recursive=True)

    with tarfile.open(archive_path, read_mode) as archive:
        assert set(archive.getnames()) == {
            "parent",
            "parent/super",
            "parent/super/duper",
            "parent/super/duper/deeply",
            "parent/super/duper/deeply/nested",
            "parent/super/duper/deeply/nested/dir",
            "parent/super/duper/deeply/nested/file.txt",
        }
        assert archive.getmember("parent").isdir()
        assert archive.getmember("parent/super").isdir()
        assert archive.getmember("parent/super/duper").isdir()
        assert archive.getmember("parent/super/duper/deeply").isdir()
        assert archive.getmember("parent/super/duper/deeply/nested").isdir()
        assert archive.getmember("parent/super/duper/deeply/nested/dir").isdir()
        assert archive.getmember("parent/super/duper/deeply/nested/file.txt").isfile()


def test_adding_multi_level_directories_with_items_recursively(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "parent"
    dir_path.mkdir()

    item_file_path1 = dir_path / "file1.txt"
    item_file_path1.touch()

    item_dir_path1 = dir_path / "dir1"
    item_dir_path1.mkdir()

    nested_dir_path = dir_path / "nested"
    nested_dir_path.mkdir()

    item_file_path2 = nested_dir_path / "file2.txt"
    item_file_path2.touch()

    item_dir_path2 = nested_dir_path / "dir2"
    item_dir_path2.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, recursive=True)

    with tarfile.open(archive_path, read_mode) as archive:
        assert set(archive.getnames()) == {
            "parent",
            "parent/dir1",
            "parent/file1.txt",
            "parent/nested",
            "parent/nested/dir2",
            "parent/nested/file2.txt",
        }
        assert archive.getmember("parent").isdir()
        assert archive.getmember("parent/dir1").isdir()
        assert archive.getmember("parent/file1.txt").isfile()
        assert archive.getmember("parent/nested").isdir()
        assert archive.getmember("parent/nested/dir2").isdir()
        assert archive.getmember("parent/nested/file2.txt").isfile()


def test_adding_directory_with_items_non_recursively(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "parent"
    dir_path.mkdir()

    item_file_path = dir_path / "file.txt"
    item_file_path.touch()

    item_dir_path = dir_path / "dir"
    item_dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, recursive=False)
        archive.add(item_file_path, arcname="parent/file.txt")
        archive.add(item_dir_path, arcname="parent/dir")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["parent", "parent/file.txt", "parent/dir"]
        assert archive.getmember("parent").isdir()
        assert archive.getmember("parent/file.txt").isfile()
        assert archive.getmember("parent/dir").isdir()


def test_adding_directory_with_nested_items_non_recursively(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "parent"
    dir_path.mkdir()

    nested_dir_path = dir_path / "nested"
    nested_dir_path.mkdir()

    item_file_path = nested_dir_path / "file.txt"
    item_file_path.touch()

    item_dir_path = nested_dir_path / "dir"
    item_dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, recursive=False)
        archive.add(nested_dir_path, recursive=False, arcname="parent/nested")
        archive.add(item_file_path, arcname="parent/nested/file.txt")
        archive.add(item_dir_path, arcname="parent/nested/dir")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == [
            "parent",
            "parent/nested",
            "parent/nested/file.txt",
            "parent/nested/dir",
        ]
        assert archive.getmember("parent").isdir()
        assert archive.getmember("parent/nested").isdir()
        assert archive.getmember("parent/nested/file.txt").isfile()
        assert archive.getmember("parent/nested/dir").isdir()


def test_adding_directory_with_deeply_nested_items_non_recursively(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "parent"
    dir_path.mkdir()

    nested_dir_path = dir_path / "deeply" / "nested"
    nested_dir_path.mkdir(parents=True)

    item_file_path = nested_dir_path / "file.txt"
    item_file_path.touch()

    item_dir_path = nested_dir_path / "dir"
    item_dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, recursive=False)
        archive.add(nested_dir_path, recursive=False, arcname="parent/deeply/nested")
        archive.add(item_file_path, arcname="parent/deeply/nested/file.txt")
        archive.add(item_dir_path, arcname="parent/deeply/nested/dir")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == [
            "parent",
            "parent/deeply/nested",
            "parent/deeply/nested/file.txt",
            "parent/deeply/nested/dir",
        ]
        assert archive.getmember("parent").isdir()
        assert archive.getmember("parent/deeply/nested").isdir()
        assert archive.getmember("parent/deeply/nested/file.txt").isfile()
        assert archive.getmember("parent/deeply/nested/dir").isdir()


def test_adding_directory_non_recursively_does_not_add_its_items(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "parent"
    dir_path.mkdir()

    item_file_path1 = dir_path / "file1.txt"
    item_file_path1.touch()

    item_dir_path1 = dir_path / "dir1"
    item_dir_path1.mkdir()

    nested_dir_path = dir_path / "nested"
    nested_dir_path.mkdir()

    item_file_path2 = nested_dir_path / "file2.txt"
    item_file_path2.touch()

    item_dir_path2 = nested_dir_path / "dir2"
    item_dir_path2.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, recursive=False)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["parent"]
        assert archive.getmember("parent").isdir()


def test_adding_directory_without_items_recursively(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "parent"
    dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, recursive=True)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["parent"]
        assert archive.getmember("parent").isdir()


def test_directory_items_are_added_recursively_by_default(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path = tmp_path / "parent"
    dir_path.mkdir()

    item_file_path = dir_path / "file.txt"
    item_file_path.touch()

    item_dir_path = dir_path / "dir"
    item_dir_path.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path, recursive=True)

    with tarfile.open(archive_path, read_mode) as archive:
        assert set(archive.getnames()) == {"parent", "parent/dir", "parent/file.txt"}
        assert archive.getmember("parent").isdir()
        assert archive.getmember("parent/dir").isdir()
        assert archive.getmember("parent/file.txt").isfile()


def test_member_names_are_not_limited_by_file_system_file_type_nesting_rules(
    tmp_path, archive_path, write_mode, read_mode
):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path, arcname="file1.txt")
        archive.add(file_path, arcname="file1.txt/file2.txt")

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == [
            "file1.txt",
            "file1.txt/file2.txt",
        ]
        assert archive.getmember("file1.txt").isfile()
        assert archive.getmember("file1.txt/file2.txt").isfile()


def test_file_contents_are_preserved(tmp_path, archive_path, write_mode, read_mode):
    file_path = tmp_path / "file.txt"
    file_content = "This is some test content."
    file_path.write_text(file_content)

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path)

    with tarfile.open(archive_path, read_mode) as archive:
        extracted_file = archive.extractfile("file.txt")
        assert extracted_file is not None

        extracted_content = extracted_file.read().decode()
        assert extracted_content == file_content


@pytest.mark.parametrize("permissions", [0o644, 0o600, 0o755, 0o700])
def test_file_permissions_are_preserved(
    tmp_path, archive_path, write_mode, read_mode, permissions
):
    file_path = tmp_path / "file.txt"
    file_path.touch()
    file_path.chmod(permissions)

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path)

    with tarfile.open(archive_path, read_mode) as archive:
        member = archive.getmember("file.txt")
        assert member.mode & 0o777 == permissions


@pytest.mark.parametrize("permissions", [0o755, 0o700, 0o775, 0o777])
def test_directory_permissions_are_preserved(
    tmp_path, archive_path, write_mode, read_mode, permissions
):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()
    dir_path.chmod(permissions)

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path)

    with tarfile.open(archive_path, read_mode) as archive:
        member = archive.getmember("dir")
        assert member.mode & 0o777 == permissions


def test_add_dereferences_symlinks_if_option_is_true(
    tmp_path, archive_path, write_mode, read_mode
):
    target_file_path = tmp_path / "target.txt"
    target_file_content = "This is some test content."
    target_file_path.write_text(target_file_content)

    symlink_path = tmp_path / "symlink.txt"
    symlink_path.symlink_to(target_file_path)

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(symlink_path, dereference=True)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["symlink.txt"]
        assert archive.getmember("symlink.txt").isreg()

        extracted_file = archive.extractfile("symlink.txt")
        assert extracted_file is not None

        extracted_content = extracted_file.read().decode()
        assert extracted_content == target_file_content


def test_add_does_not_dereference_symlinks_if_option_is_false(
    tmp_path, archive_path, write_mode, read_mode
):
    target_file_path = tmp_path / "target.txt"
    target_file_path.touch()

    symlink_path = tmp_path / "symlink.txt"
    symlink_path.symlink_to(target_file_path.relative_to(symlink_path.parent))

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(symlink_path, dereference=False)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["symlink.txt"]
        member = archive.getmember("symlink.txt")
        assert member.issym()
        assert member.linkname == "target.txt"


def test_add_does_not_dereference_symlinks_by_default(
    tmp_path, archive_path, write_mode, read_mode
):
    target_file_path = tmp_path / "target.txt"
    target_file_path.touch()

    symlink_path = tmp_path / "symlink.txt"
    symlink_path.symlink_to(target_file_path.relative_to(symlink_path.parent))

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(symlink_path)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["symlink.txt"]
        member = archive.getmember("symlink.txt")
        assert member.issym()
        assert member.linkname == "target.txt"


def test_add_raises_if_dereferencing_symlink_to_non_existing_path(
    tmp_path, archive_path, write_mode
):
    symlink_path = tmp_path / "symlink.txt"
    symlink_path.symlink_to("non_existing_target.txt")

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        with pytest.raises(RuntimeError, match="path does not exist"):
            archive.add(symlink_path, dereference=True)


def test_file_addition_order_is_preserved(
    tmp_path, archive_path, write_mode, read_mode
):
    file_path1 = tmp_path / "file1.txt"
    file_path1.touch()

    file_path2 = tmp_path / "file2.txt"
    file_path2.touch()

    file_path3 = tmp_path / "file3.txt"
    file_path3.touch()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(file_path2)
        archive.add(file_path1)
        archive.add(file_path3)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["file2.txt", "file1.txt", "file3.txt"]


def test_directory_addition_order_is_preserved(
    tmp_path, archive_path, write_mode, read_mode
):
    dir_path1 = tmp_path / "dir1"
    dir_path1.mkdir()

    dir_path2 = tmp_path / "dir2"
    dir_path2.mkdir()

    dir_path3 = tmp_path / "dir3"
    dir_path3.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path2)
        archive.add(dir_path1)
        archive.add(dir_path3)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["dir2", "dir1", "dir3"]


def test_file_and_directory_addition_order_is_preserved(
    tmp_path, archive_path, write_mode, read_mode
):
    file_path1 = tmp_path / "a"
    file_path1.touch()

    file_path2 = tmp_path / "b"
    file_path2.touch()

    dir_path1 = tmp_path / "c"
    dir_path1.mkdir()

    dir_path2 = tmp_path / "d"
    dir_path2.mkdir()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        archive.add(dir_path2)
        archive.add(file_path1)
        archive.add(file_path2)
        archive.add(dir_path1)

    with tarfile.open(archive_path, read_mode) as archive:
        assert archive.getnames() == ["d", "a", "b", "c"]


def test_arcnames_must_be_relative(tmp_path, archive_path, write_mode):
    file_path = tmp_path / "file.txt"
    file_path.touch()

    with ArchiveWriter.open(archive_path, write_mode) as archive:
        with pytest.raises(
            OSError, match="paths in archives must be relative when setting path for"
        ):
            archive.add(file_path, arcname="/absolute/path/file.txt")
