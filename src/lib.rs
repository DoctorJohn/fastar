use flate2::read::GzDecoder;
use flate2::write::GzEncoder;
use flate2::Compression;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyType};
use std::fs::File;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use tar::Archive;

#[pyclass]
struct ArchiveWriter {
    builder: Option<tar::Builder<Box<dyn Write + Send + Sync>>>,
}

#[pymethods]
impl ArchiveWriter {
    #[classmethod]
    #[pyo3(signature = (path, mode="w:gz"))]
    fn open(
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
            _ => Err(PyRuntimeError::new_err(
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
            .ok_or_else(|| PyRuntimeError::new_err("archive is already closed"))?;

        builder.follow_symlinks(dereference);

        let default_name = || -> PyResult<String> {
            let name = Path::new(&path)
                .file_name()
                .ok_or_else(|| PyRuntimeError::new_err("cannot derive name from path"))?
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

#[pyclass(unsendable)]
struct ArchiveReader {
    archive: Option<Archive<Box<dyn Read>>>,
}

#[pymethods]
impl ArchiveReader {
    #[classmethod]
    #[pyo3(signature = (path, mode="r:gz"))]
    fn open(
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
            _ => Err(PyRuntimeError::new_err(
                "unsupported mode; only 'r' and 'r:gz' are supported",
            )),
        }
    }

    fn extract(&mut self, to: PathBuf) -> PyResult<()> {
        let archive = self
            .archive
            .as_mut()
            .ok_or_else(|| PyRuntimeError::new_err("archive is already closed"))?;

        archive.unpack(to)?;
        Ok(())
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

#[pyfunction]
#[pyo3(signature = (path, mode))]
fn open(py: Python<'_>, path: PathBuf, mode: &str) -> PyResult<PyObject> {
    match mode {
        "w" | "w:gz" => {
            let writer = ArchiveWriter::open(&py.get_type::<ArchiveWriter>(), py, path, mode)?;
            Ok(writer.into())
        }
        "r" | "r:gz" => {
            let reader = ArchiveReader::open(&py.get_type::<ArchiveReader>(), py, path, mode)?;
            Ok(reader.into())
        }
        _ => Err(PyRuntimeError::new_err(
            "unsupported mode; supported modes are 'w', 'w:gz', 'r', 'r:gz'",
        )),
    }
}

#[pymodule]
fn fastar(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ArchiveWriter>()?;
    m.add_class::<ArchiveReader>()?;
    m.add_function(wrap_pyfunction!(open, m)?)?;
    Ok(())
}
