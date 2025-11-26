use pyo3::prelude::*;
use std::io::Read;
use tar::{Entry, EntryType};

#[pyclass]
pub struct ArchiveEntry {
    entry_type: EntryType,

    #[pyo3(get)]
    pub name: String,

    #[pyo3(get)]
    pub mode: u32,

    #[pyo3(get)]
    pub size: u64,

    #[pyo3(get)]
    pub mtime: u64,

    #[pyo3(get)]
    pub link_name: Option<String>,
}

impl ArchiveEntry {
    pub fn new<R: Read>(entry: &Entry<R>) -> PyResult<Self> {
        let name = entry.path()?.to_string_lossy().into_owned();
        let mode = entry.header().mode()?;
        let size = entry.header().size()?;
        let mtime = entry.header().mtime()?;

        let link_name: Option<String> = match entry.link_name()? {
            Some(path) => Some(path.to_string_lossy().into_owned()),
            None => None,
        };

        Ok(Self {
            entry_type: entry.header().entry_type(),
            name,
            mode,
            size,
            mtime,
            link_name,
        })
    }
}

#[pymethods]
impl ArchiveEntry {
    pub fn is_dir(&self) -> bool {
        self.entry_type.is_dir()
    }

    pub fn is_file(&self) -> bool {
        self.entry_type.is_file()
    }

    pub fn is_symlink(&self) -> bool {
        self.entry_type.is_symlink()
    }
}
