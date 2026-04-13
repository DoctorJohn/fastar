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
    builder: Option<tar::Builder<ArchiveWriterInner>>,
}

#[pymethods]
impl ArchiveWriter {
    #[classmethod]
    #[pyo3(signature = (path, mode, sparse=true))]
    pub fn open(
        _cls: &Bound<'_, PyType>,
        py: Python<'_>,
        path: PathBuf,
        mode: &str,
        sparse: bool,
    ) -> PyResult<Py<ArchiveWriter>> {
        match mode {
            "w:gz" => {
                let file = File::create(path)?;
                let enc = GzEncoder::new(file, Compression::default());
                let mut builder = tar::Builder::new(ArchiveWriterInner::Gzip(enc));
                builder.sparse(sparse);
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
                let mut builder = tar::Builder::new(ArchiveWriterInner::Zstd(enc));
                builder.sparse(sparse);
                Py::new(
                    py,
                    ArchiveWriter {
                        builder: Some(builder),
                    },
                )
            }
            "w" => {
                let file = File::create(path)?;
                let mut builder = tar::Builder::new(ArchiveWriterInner::Uncompressed(file));
                builder.sparse(sparse);
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
            let writer = builder.into_inner()?;
            writer.finish()?;
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

enum ArchiveWriterInner {
    Uncompressed(File),
    Gzip(GzEncoder<File>),
    Zstd(ZstdEncoder<'static, File>),
}

impl Write for ArchiveWriterInner {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        match self {
            Self::Uncompressed(w) => w.write(buf),
            Self::Gzip(w) => w.write(buf),
            Self::Zstd(w) => w.write(buf),
        }
    }
    fn flush(&mut self) -> std::io::Result<()> {
        match self {
            Self::Uncompressed(w) => w.flush(),
            Self::Gzip(w) => w.flush(),
            Self::Zstd(w) => w.flush(),
        }
    }
}

impl ArchiveWriterInner {
    fn finish(self) -> std::io::Result<()> {
        match self {
            Self::Zstd(enc) => {
                enc.finish()?;
                Ok(())
            }
            Self::Gzip(enc) => {
                enc.finish()?;
                Ok(())
            }
            Self::Uncompressed(mut f) => f.flush(),
        }
    }
}
