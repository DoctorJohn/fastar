from typing import Literal, Optional, Union, overload
from typing_extensions import Self
from pathlib import Path
from os import PathLike

class FastarError(Exception):
    """Base exception for all fastar errors."""

class ArchiveClosedError(FastarError):
    """Exception raised when attempting to use a closed archive."""

class NameDerivationError(FastarError):
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
        """

    def add(
        self,
        path: Union[str, Path, PathLike[str]],
        arcname: Optional[str] = None,
        recursive: bool = True,
        dereference: bool = False,
    ) -> None:
        """
        Add a file or directory to the archive.

        Args:
            path: Path to the file or directory to add
            arcname: Name to use in the archive (defaults to the filename)
            recursive: If True and path is a directory, add all contents recursively
            dereference: If True, add the target of symlinks instead of the symlink itself

        Raises:
            ArchiveClosedError: If the archive is already closed
            NameDerivationError: If arcname is not provided and name cannot be derived from path
            RuntimeError: If the path doesn't exist
        """

    def close(self) -> None:
        """
        Close the archive and flush all pending writes.

        Raises:
            RuntimeError: If there's an error flushing the writer
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
            IOError: If the file cannot be opened
        """

    def extract(self, to: Union[str, Path, PathLike[str]]) -> None:
        """
        Extract all contents of the archive to the specified directory.

        Args:
            to: Destination directory path

        Raises:
            ArchiveClosedError: If the archive is already closed
            IOError: If extraction fails
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
        IOError: If the file cannot be opened
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
        IOError: If the file cannot be opened
    """
