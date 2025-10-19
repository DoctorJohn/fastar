use flate2::read::GzDecoder;
use pyo3::prelude::*;
use std::fs::File;
use tar::Archive;

#[pyfunction]
fn untar_gz(tar_gz_path: String, destination_path: String) -> PyResult<()> {
    let tar_gz = File::open(tar_gz_path)?;
    let tar = GzDecoder::new(tar_gz);
    let mut archive = Archive::new(tar);
    archive.unpack(destination_path)?;
    Ok(())
}

#[pymodule]
fn fastar(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(untar_gz, m)?)?;
    Ok(())
}
