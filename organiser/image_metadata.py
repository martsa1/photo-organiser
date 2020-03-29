"""Module collecting functions related to image metadata."""

import exifread
from typing import Dict, List
import io
import logging
import pendulum

from organiser.types import FileTarget


LOG = logging.getLogger(__name__)


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


def parse_image_meta_for_file_target(target: FileTarget) -> FileTarget:
    """Wrap get_file_meta for use within RX pipelines."""
    if target.file_contents:
        target.image_metadata = get_file_meta(target.file_contents)

    return target


def identify_image_datestamp(target: FileTarget) -> FileTarget:
    """Attempt to process image metadata for FileTarget, setting FileTarget.datestamp on success."""
    known_date_fields = ("EXIF DateTimeDigitized", "EXIF DateTimeOriginal", "Image DateTime")

    possible_datestamps: List[str] = []
    for field in known_date_fields:
        target_date = target.image_metadata.get(field, None)
        if target_date:
            possible_datestamps.append(target_date.printable)

    parsed_datestamps: List[pendulum.DateTime] = []
    for datestamp in possible_datestamps:
        try:
            parsed_datestamps.append(pendulum.parse(datestamp))
        except pendulum.exceptions.PendulumException:
            LOG.debug("Unable to parse %s into a native DateTime.", datestamp)
            pass

    if not parsed_datestamps:
        LOG.info("Unable to identify image datestamp")
        return target

    if len(parsed_datestamps) == 1:
        LOG.debug("Date fields seem to agree with one another")
        target.datestamp = parsed_datestamps[0]

    else:
        # Take the newest one - This is somewhat arbitrary...
        LOG.debug("Date fields did not agree with one another: %s", parsed_datestamps)
        target.datestamp = min(parsed_datestamps)

    return target
