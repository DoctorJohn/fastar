use pyo3::create_exception;
use pyo3::exceptions::PyException;

create_exception!(fastar, FastarError, PyException);
create_exception!(fastar, ArchiveClosedError, FastarError);
create_exception!(fastar, ArchiveUnpackingError, FastarError);
create_exception!(fastar, ArchiveAppendingError, FastarError);
create_exception!(fastar, NameDerivationError, ArchiveAppendingError);
