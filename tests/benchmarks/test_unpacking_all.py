import sys

import fastar

if sys.version_info >= (3, 9) and sys.version_info < (3, 14):
    from backports.zstd import tarfile
else:
    import tarfile


def test_benchmark_unpacking_all_with_tarfile(
    benchmark, large_archive_path, read_mode, target_path
):
    def read_archive():
        with tarfile.open(large_archive_path, read_mode) as archive:
            archive.extractall(target_path)

    benchmark(read_archive)


def test_benchmark_unpacking_all_with_fastar(
    benchmark, large_archive_path, read_mode, target_path
):
    def read_archive():
        with fastar.open(large_archive_path, read_mode) as archive:
            archive.unpack(target_path)

    benchmark(read_archive)


def test_benchmark_unpacking_all_without_mtime_using_fastar(
    benchmark, large_archive_path, read_mode, target_path
):
    def read_archive():
        with fastar.open(large_archive_path, read_mode) as archive:
            archive.unpack(target_path, preserve_mtime=False)

    benchmark(read_archive)
