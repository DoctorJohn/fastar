mod errors;
mod reader;
mod writer;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::path::PathBuf;

use errors::*;
use reader::ArchiveReader;
use writer::ArchiveWriter;

#[pyfunction]
#[pyo3(signature = (path, mode))]
fn open(py: Python<'_>, path: PathBuf, mode: &str) -> PyResult<PyObject> {
    match mode {
        "w" | "w:gz" | "w:zst" => {
            let writer = ArchiveWriter::open(&py.get_type::<ArchiveWriter>(), py, path, mode)?;
            Ok(writer.into())
        }
        "r" | "r:gz" | "r:zst" => {
            let reader = ArchiveReader::open(&py.get_type::<ArchiveReader>(), py, path, mode)?;
            Ok(reader.into())
        }
        _ => Err(PyValueError::new_err(
            "unsupported mode; supported modes are 'w', 'w:gz', 'w:zst', 'r', 'r:gz', 'r:zst'",
        )),
    }
}

#[pymodule]
fn fastar(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ArchiveWriter>()?;
    m.add_class::<ArchiveReader>()?;
    m.add_function(wrap_pyfunction!(open, m)?)?;
    m.add("FastarError", m.py().get_type::<errors::FastarError>())?;
    m.add(
        "ArchiveClosedError",
        m.py().get_type::<ArchiveClosedError>(),
    )?;
    m.add(
        "NameDerivationError",
        m.py().get_type::<NameDerivationError>(),
    )?;
    m.add(
        "ArchiveAppendingError",
        m.py().get_type::<ArchiveAppendingError>(),
    )?;
    m.add(
        "ArchiveUnpackingError",
        m.py().get_type::<ArchiveUnpackingError>(),
    )?;
    Ok(())
}
