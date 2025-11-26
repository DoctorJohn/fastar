import sys

import fastar

if sys.version_info >= (3, 9) and sys.version_info < (3, 14):
    from backports.zstd import tarfile
else:
    import tarfile


def test_benchmark_appending_incrementally_with_tarfile(
    benchmark, large_source_path, archive_path, write_mode
):
    files = list(large_source_path.glob("*.txt"))

    def append_files():
        with tarfile.open(archive_path, write_mode) as archive:
            for file_path in files:
                archive.add(file_path)

    benchmark(append_files)


def test_benchmark_appending_incrementally_with_fastar(
    benchmark, large_source_path, archive_path, write_mode
):
    files = list(large_source_path.glob("*.txt"))

    def append_files():
        with fastar.open(archive_path, write_mode) as archive:
            for file_path in files:
                archive.append(file_path)

    benchmark(append_files)
