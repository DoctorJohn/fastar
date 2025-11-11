use crate::errors::{ArchiveClosedError, NameDerivationError, UnsupportedModeError};
use flate2::write::GzEncoder;
use flate2::Compression;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyType};
use std::fs::File;
use std::io::Write;
use std::path::{Path, PathBuf};

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
            _ => Err(UnsupportedModeError::new_err(
                "unsupported mode; only 'w' and 'w:gz' are supported",
            )),
        }
    }

    #[pyo3(signature = (path, arcname=None, recursive=true, dereference=false))]
    fn add(
        &mut self,
        path: PathBuf,
        arcname: Option<String>,
        recursive: bool,
        dereference: bool,
    ) -> PyResult<()> {
        let builder = self
            .builder
            .as_mut()
            .ok_or_else(|| ArchiveClosedError::new_err("archive is already closed"))?;

        builder.follow_symlinks(dereference);

        let default_name = || -> PyResult<String> {
            let name = Path::new(&path)
                .file_name()
                .ok_or_else(|| NameDerivationError::new_err("cannot derive name from path"))?
                .to_string_lossy()
                .into_owned();
            Ok(name)
        }()?;

        let name = arcname.unwrap_or(default_name);

        if path.is_dir() {
            if recursive {
                builder.append_dir_all(&name, &path)?;
            } else {
                builder.append_dir(&name, &path)?;
            }
        } else if path.is_file() {
            builder.append_path_with_name(&path, &name)?;
        } else {
            return Err(PyRuntimeError::new_err("path does not exist"));
        }
        Ok(())
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
