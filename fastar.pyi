from os import PathLike
from pathlib import Path
from typing import Literal, Optional, Union, overload

from typing_extensions import Self

class FastarError(Exception):
    """Base exception for all fastar errors."""

class ArchiveClosedError(FastarError):
    """Exception raised when attempting to use a closed archive."""

class ArchiveUnpackingError(FastarError):
    """Exception raised when unpacking an archive fails."""

class ArchiveAppendingError(FastarError):
    """Exception raised when appending to an archive fails."""

class NameDerivationError(ArchiveAppendingError):
    """Exception raised when a file name cannot be derived from a path."""

class ArchiveWriter:
    """A tar archive writer that supports compressed and uncompressed formats."""

    @classmethod
    def open(
        cls, path: Union[str, Path, PathLike[str]], mode: Literal["w", "w:gz"] = "w:gz"
    ) -> Self:
        """
        Open a tar archive for writing.

        Args:
            path: Path to the archive file to create
            mode: Write mode - 'w' for uncompressed, 'w:gz' for gzip compressed (default)

        Returns:
            An ArchiveWriter instance

        Raises:
            ValueError: If an unsupported mode is provided
            OSError: If the file cannot be opened
        """

    def append(
        self,
        path: Union[str, Path, PathLike[str]],
        arcname: Optional[Union[str, Path, PathLike[str]]] = None,
        recursive: bool = True,
        dereference: bool = False,
    ) -> None:
        """
        Append a file or directory to the archive.

        Args:
            path: Path to the file or directory to append
            arcname: Name to use in the archive (defaults to the filename)
            recursive: If True and path is a directory, append all contents recursively
            dereference: If True, append the target of symlinks instead of the symlink itself

        Raises:
            ArchiveClosedError: If the archive is already closed
            ArchiveAppendingError: If the target cannot be appended to the archive
            OSError: If there's an error reading the target file or directory
        """

    def close(self) -> None:
        """
        Close the archive and flush all pending writes.

        Raises:
            OSError: If there's an error flushing the archive
        """

    def __enter__(self) -> Self:
        """Enter the context manager."""

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """Exit the context manager, closing the archive."""

class ArchiveReader:
    """A tar archive reader that supports compressed and uncompressed formats."""

    @classmethod
    def open(
        cls, path: Union[str, Path, PathLike[str]], mode: Literal["r", "r:gz"] = "r:gz"
    ) -> Self:
        """
        Open a tar archive for reading.

        Args:
            path: Path to the archive file to read
            mode: Read mode - 'r' for uncompressed, 'r:gz' for gzip compressed (default)

        Returns:
            An ArchiveReader instance

        Raises:
            ValueError: If an unsupported mode is provided
            OSError: If the file cannot be opened
        """

    def unpack(
        self, to: Union[str, Path, PathLike[str]], preserve_mtime: bool = True
    ) -> None:
        """
        Unpack all contents of the archive and put them into the specified directory.

        Args:
            to: Destination directory path
            preserve_mtime: whether to preserve file modification times

        Raises:
            ArchiveClosedError: If the archive is already closed
            ArchiveUnpackingError: If the archive cannot be unpacked
            OSError: If unpacking fails due to I/O errors
        """

    def close(self) -> None:
        """Close the archive."""

    def __enter__(self) -> Self:
        """Enter the context manager."""

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """Exit the context manager, closing the archive."""

@overload
def open(
    path: Union[str, Path, PathLike[str]], mode: Literal["w", "w:gz"]
) -> ArchiveWriter:
    """
    Open a tar archive for writing.

    Args:
        path: Path to the archive file to create
        mode: Write mode - 'w' for uncompressed, 'w:gz' for gzip compressed

    Returns:
        An ArchiveWriter instance

    Raises:
        ValueError: If an unsupported mode is provided
        OSError: If the file cannot be opened
    """

@overload
def open(
    path: Union[str, Path, PathLike[str]], mode: Literal["r", "r:gz"]
) -> ArchiveReader:
    """
    Open a tar archive for reading.

    Args:
        path: Path to the archive file to read
        mode: Read mode - 'r' for uncompressed, 'r:gz' for gzip compressed

    Returns:
        An ArchiveReader instance

    Raises:
        ValueError: If an unsupported mode is provided
        OSError: If the file cannot be opened
    """
