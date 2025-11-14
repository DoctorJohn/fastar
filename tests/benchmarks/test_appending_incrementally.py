import tarfile

import fastar


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
