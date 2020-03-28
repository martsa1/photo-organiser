"""Module collecting functions related to image metadata."""

import exifread
from typing import Dict
import io

def get_file_meta(file_content: bytes) -> Dict[str, exifread.classes.IfdTag]:
    """Retrieve metadata for the provided file data."""
    file_stream = io.BytesIO(file_content)

    file_exif_data = exifread.process_file(file_stream)
    file_exif_data = {
        tag: file_exif_data[tag]
        for tag in file_exif_data
        if tag not in (
            'EXIF MakerNote',
            'JPEGThumbnail',
            'TIFFThumbnail',
        )
    }

    del file_stream

    return file_exif_data

def temp_load_from_filepath(target: str) -> bytes:
    """Temporary convenience function, returns a file's contents from a file path as bytes."""
    with open(target, "rb") as file_handle:
        return file_handle.read()
