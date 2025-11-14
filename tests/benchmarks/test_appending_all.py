import tarfile

import fastar


def test_benchmark_appending_all_with_tarfile(
    benchmark, archive_path, write_mode, large_source_path
):
    def create_archive():
        with tarfile.open(archive_path, write_mode) as archive:
            archive.add(large_source_path, recursive=True)

    benchmark(create_archive)


def test_benchmark_appending_all_with_fastar(
    benchmark, archive_path, write_mode, large_source_path
):
    def create_archive():
        with fastar.open(archive_path, write_mode) as archive:
            archive.append(large_source_path, recursive=True)

    benchmark(create_archive)
