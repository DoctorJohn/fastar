import shutil
import subprocess

import pytest

import fastar


@pytest.mark.skipif(
    shutil.which("tar") is None,
    reason="GNU tar is not available on this system",
)
def test_zstd(source_path, archive_path, write_mode, target_path):
    file_path = source_path / "file.txt"
    file_path.touch()

    with fastar.open(archive_path, write_mode) as writer:
        writer.append(file_path)

    subprocess.run(
        ["tar", "-xvf", str(archive_path), "-C", str(target_path)],
        check=True,
    )

    output_file = target_path / "file.txt"
    assert output_file.exists()
