#!/usr/bin/env python
import logging

import fire
import rx
from rx import operators

from organiser import file_listing as fl
from organiser import filename_calculations as fc
from organiser import image_metadata as im
from organiser.types import FileTarget

LOG = logging.getLogger(__name__)


def main(base_dir: str = "", storage_dir: str = "", copy_only: bool = False) -> None:
    """Organise image files from one location to another.

    This application allows you to specify a base directory from which to
    recursively search for image files, and to organise those files, based on
    the date they were taken,into a collection of year and month folders.  The
    application will respect albums which already exist based on the presence
    of an album name.

    By setting the --copy-only flag, this application will copy, rather than
    the default move, files when organising them.

    Arguments:
        base_dir: The location from which the application should search for
            image files.
        storage_dir: The location from which the application should create the
            archive of organised files.
        copy_only: A flag to request that we make copies of files, rather than
            moving them.
    """

    if not storage_dir:
        storage_dir = base_dir

    file_listing = rx.from_iterable(
        fl.file_listing_iterator(base_dir, r'.*(?:jpg|JPG|JPEG|jpeg)$'),
    )

    hashed_files = file_listing.pipe(
        operators.map(fl.load_file_contents),
        operators.map(fl.sha256_file),
        operators.map(fl.encode_shasum),
    )

    files_with_metadata = hashed_files.pipe(
        operators.map(im.parse_image_meta_for_file_target),
        operators.map(im.identify_image_datestamp),
    )

    files_with_move_path = files_with_metadata.pipe(
        operators.map(lambda target: fc.identify_photo_move_path(storage_dir, target)),
        operators.map(lambda target: target.clear_contents_data()),
    )

    # TODO - Add duplicate file checks in here!!

    move_operations = files_with_move_path.pipe(
            operators.map(lambda target: (target.file_path, target.target_move_path)),
    )

    def printer(target: FileTarget) -> str:
        """Temp printer closure."""
        return (
            f"File Target:\n"
            f"   Path: {target.file_path}\n"
            f"   Hash: {target.encoded_hash}\n"
            f"   Target Path: {target.target_move_path}\n"
            f"   Image taken at: {target.image_metadata.get('EXIF DateTimeOriginal', 'Unknown')}"
        )

    move_operations.subscribe(
        on_next=lambda target: print(target),
        on_error=lambda err: print(err),
        on_completed=lambda: print("Done"),
    )


if __name__ == '__main__':
    fire.Fire(main)
