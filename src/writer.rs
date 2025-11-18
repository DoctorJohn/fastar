use crate::errors::*;
use flate2::write::GzEncoder;
use flate2::Compression;
use pyo3::exceptions::{PyFileNotFoundError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyType};
use std::fs::File;
use std::io::{ErrorKind, Write};
use std::path::PathBuf;
use zstd::stream::write::Encoder as ZstdEncoder;

#[pyclass]
pub struct ArchiveWriter {
    builder: Option<tar::Builder<Box<dyn Write + Send + Sync>>>,
}

#[pymethods]
impl ArchiveWriter {
    #[classmethod]
    #[pyo3(signature = (path, mode="w:gz"))]
    pub fn open(
        _cls: &Bound<'_, PyType>,
        py: Python<'_>,
        path: PathBuf,
        mode: &str,
    ) -> PyResult<Py<ArchiveWriter>> {
        match mode {
            "w:gz" => {
                let file = File::create(path)?;
                let enc = GzEncoder::new(file, Compression::default());
                let writer: Box<dyn Write + Send + Sync> = Box::new(enc);
                let builder = tar::Builder::new(writer);
                Py::new(
                    py,
                    ArchiveWriter {
                        builder: Some(builder),
                    },
                )
            }
            "w:zst" => {
                let file = File::create(path)?;
                let enc = ZstdEncoder::new(file, 0)?; // default compression level
                let writer: Box<dyn Write + Send + Sync> = Box::new(enc);
                let builder = tar::Builder::new(writer);
                Py::new(
                    py,
                    ArchiveWriter {
                        builder: Some(builder),
                    },
                )
            }
            "w" => {
                let file = File::create(path)?;
                let writer: Box<dyn Write + Send + Sync> = Box::new(file);
                let builder = tar::Builder::new(writer);
                Py::new(
                    py,
                    ArchiveWriter {
                        builder: Some(builder),
                    },
                )
            }
            _ => Err(PyValueError::new_err(
                "unsupported mode; only 'w', 'w:gz', and 'w:zst' are supported",
            )),
        }
    }

    #[pyo3(signature = (path, arcname=None, recursive=true, dereference=false))]
    fn append(
        &mut self,
        path: PathBuf,
        arcname: Option<PathBuf>,
        recursive: bool,
        dereference: bool,
    ) -> PyResult<()> {
        let builder = self
            .builder
            .as_mut()
            .ok_or_else(|| ArchiveClosedError::new_err("archive is already closed"))?;

        builder.follow_symlinks(dereference);

        let name = arcname
            .unwrap_or(PathBuf::from(path.file_name().ok_or_else(|| {
                NameDerivationError::new_err("cannot derive name from path")
            })?));

        if path.is_dir() {
            if recursive {
                builder.append_dir_all(&name, &path)
            } else {
                builder.append_dir(&name, &path)
            }
        } else if path.is_file() {
            builder.append_path_with_name(&path, &name)
        } else {
            return Err(PyFileNotFoundError::new_err(format!(
                "path does not exist: {}",
                path.display()
            )));
        }
        .map_err(|e: std::io::Error| {
            if e.kind() == ErrorKind::Other {
                ArchiveAppendingError::new_err(e.to_string())
            } else {
                e.into()
            }
        })
    }

    fn close(&mut self) -> PyResult<()> {
        if let Some(builder) = self.builder.take() {
            let mut writer = builder.into_inner()?;
            writer.flush()?;
        }
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
