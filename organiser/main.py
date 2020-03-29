#!/usr/bin/env python
import logging
from typing import List

import fire
import rx
from rx import operators
from better_exceptions import patch_logging

from organiser import file_listing as fl
from organiser import file_ops as fo
from organiser import filename_calculations as fc
from organiser import image_metadata as im
from organiser.types import FileTarget

LOG = logging.getLogger(__name__)
patch_logging()


def dry_run_print(target: FileTarget) -> None:
    """Print the dry run changes"""
    print(
        f"File Target:\n"
        f"   Current Path: {target.file_path}\n"
        f"   New Path: {target.target_move_path}\n"
        f"   Hash: {target.encoded_hash}\n"
        f"   Date taken: {target.image_metadata.get('EXIF DateTimeOriginal', 'Unknown')}"
    )


def main(
        base_dir: str = "",
        storage_dir: str = "",
        filter_regex: str = r".*(?:jpg|JPG|JPEG|jpeg)$",
        copy_only: bool = False,
        dry_run: bool = False,
) -> None:
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
        filter_regex: The python Regular Expression used to select files to
            operate on.
        copy_only: A flag to request that we make copies of files, rather than
            moving them.
        dry_run: A flag to print proposed changes only, don't actually do
            anything.
    """
    if not storage_dir:
        storage_dir = base_dir

    file_listing = rx.from_iterable(fl.file_listing_iterator(base_dir, filter_regex), )

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

    # ADD RX to filter duplicates out at this point, FileTarget == FileTarget
    # should be sufficient.
    # TODO - Add duplicate file checks in here!!

    if dry_run:
        files_with_move_path.subscribe(
            on_next=lambda target: dry_run_print(target),
            on_error=lambda err: print(err),
            on_completed=lambda: print("File processing complete."),
        )

        return

    moved_files = files_with_move_path.pipe(
        operators.map(lambda target: fo.migrate_file_target(target, copy_only)),
        #  operators.map(lambda target: completed_targets.append(target)),
    )

    moved_files.subscribe(
        on_next=lambda target: print(
            f"{'Copied' if copy_only else 'Moved'} {target.file_path} to {target.target_move_path}."
        ),
        on_error=lambda err: LOG.exception(
            "Application hit an error: %s",
            err,
            stack_info=True,
            exc_info=True,
        ),
        on_completed=lambda: print("File processing complete."),
    )


if __name__ == '__main__':
    try:
        fire.Fire(main)
    except KeyboardInterrupt:
        print("\n\nTerminating early due to user interruption.")
