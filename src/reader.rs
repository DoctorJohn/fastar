use crate::errors::{ArchiveClosedError, ArchiveUnpackingError};
use flate2::read::GzDecoder;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyType};
use std::fs::File;
use std::io::{ErrorKind, Read};
use std::path::PathBuf;
use tar::Archive;
use zstd::stream::read::Decoder as ZstdDecoder;

#[pyclass(unsendable)]
pub struct ArchiveReader {
    archive: Option<Archive<Box<dyn Read>>>,
}

#[pymethods]
impl ArchiveReader {
    #[classmethod]
    #[pyo3(signature = (path, mode="r:gz"))]
    pub fn open(
        _cls: &Bound<'_, PyType>,
        py: Python<'_>,
        path: PathBuf,
        mode: &str,
    ) -> PyResult<Py<ArchiveReader>> {
        match mode {
            "r:gz" => {
                let file = File::open(path)?;
                let decoder = GzDecoder::new(file);
                let reader: Box<dyn Read> = Box::new(decoder);
                let archive = Archive::new(reader);
                Py::new(
                    py,
                    ArchiveReader {
                        archive: Some(archive),
                    },
                )
            }
            "r:zst" => {
                let file = File::open(path)?;
                let decoder = ZstdDecoder::new(file)?;
                let reader: Box<dyn Read> = Box::new(decoder);
                let archive = Archive::new(reader);
                Py::new(
                    py,
                    ArchiveReader {
                        archive: Some(archive),
                    },
                )
            }
            "r" => {
                let file = File::open(path)?;
                let reader: Box<dyn Read> = Box::new(file);
                let archive = Archive::new(reader);
                Py::new(
                    py,
                    ArchiveReader {
                        archive: Some(archive),
                    },
                )
            }
            _ => Err(PyValueError::new_err(
                "unsupported mode; only 'r', 'r:gz', and 'r:zst' are supported",
            )),
        }
    }

    #[pyo3(signature = (to, preserve_mtime=true))]
    fn unpack(&mut self, to: PathBuf, preserve_mtime: bool) -> PyResult<()> {
        let archive = self
            .archive
            .as_mut()
            .ok_or_else(|| ArchiveClosedError::new_err("archive is already closed"))?;

        archive.set_preserve_mtime(preserve_mtime);

        archive.unpack(to).map_err(|e: std::io::Error| {
            if e.kind() == ErrorKind::Other {
                ArchiveUnpackingError::new_err(e.to_string())
            } else {
                e.into()
            }
        })
    }

    fn close(&mut self) -> PyResult<()> {
        self.archive.take();
        Ok(())
    }

    fn __enter__(py_self: PyRef<'_, Self>) -> PyRef<'_, Self> {
        py_self
    }

    fn __exit__(
        &mut self,
        _exc_type: Option<Bound<'_, PyAny>>,
        _exc: Option<Bound<'_, PyAny>>,
        _tb: Option<Bound<'_, PyAny>>,
    ) -> PyResult<bool> {
        self.close()?;
        Ok(false) // Propagate exceptions if any
    }
}
