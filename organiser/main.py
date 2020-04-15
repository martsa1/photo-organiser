#!/usr/bin/env python
import logging
from functools import partial
from pathlib import Path
from threading import Event
from time import sleep
from typing import List, Sequence, Union

import rx
import typer
from better_exceptions import patch_logging
from rx import operators
from rx.scheduler import ThreadPoolScheduler

from organiser import file_listing as fl
from organiser import file_ops as fo
from organiser import filename_calculations as fc
from organiser import image_metadata as im
from organiser.types import FailedTarget, FileTarget

LOG = logging.getLogger(__name__)
patch_logging()


def dry_run_print(target: FileTarget) -> None:
    """Print the dry run changes."""
    typer.echo(
        f"Moving: {target.file_path}, To: {target.target_move_path} -- "
        f"Date taken: {target.image_metadata.get('EXIF DateTimeOriginal', 'Unknown')}",
    )


def get_files(base_dir: Path, filter_regex: str, scheduler: rx.typing.Scheduler) -> rx.Observable:
    """Return an observable of files to process as FileTarget's."""
    return rx.from_iterable(
        fl.file_listing_iterator(base_dir, filter_regex),
        scheduler=scheduler,
    )


def load_file_content(file_stream: rx.Observable) -> rx.Observable:
    """Load files content from disk."""
    return file_stream.pipe(operators.map(fl.load_file_contents))


def generate_file_metadata(file_stream: rx.Observable) -> rx.Observable:
    """Add various file metadata to the FileTargets being streamed."""
    return file_stream.pipe(
        operators.map(fl.sha256_file),
        operators.map(fl.encode_shasum),
    )


def generate_image_metadata(file_stream: rx.Observable) -> rx.Observable:
    """Add image metadata to file_stream."""
    return file_stream.pipe(
        operators.map(im.parse_image_meta_for_file_target),
        operators.map(im.identify_image_datestamp),
    )


def generate_move_path(file_stream: rx.Observable, storage_dir: str) -> rx.Observable:
    """Identify the appropriate move path for files in the file_stream."""
    return file_stream.pipe(
        operators.map(lambda target: fc.identify_photo_move_path(storage_dir, target)),
        operators.map(lambda target: target.clear_contents_data()),
    )


def handle_error(err: Exception, event: Event) -> None:
    """Log the occurrence of an error, and set the shutdown event."""
    LOG.exception(
        "Application hit an error: %s",
        err,
        stack_info=True,
        exc_info=True,
    )
    event.set()


def filter_errors(
        item: Union[FileTarget, FailedTarget],
        error_collection: Sequence[FailedTarget],
) -> bool:
    """Filter to remove failed records, push them to error_collection for later processing.

    Suggest that callers wrap this with partial, to provide the
    error_collection, and use the resulting partial directly in
    `operators.filter` calls.
    """
    if not isinstance(item, FailedTarget):
        return True

    typer.secho(
        f"Processing for {item.original_record.file_path} failed: {item.failure_reason}",
        fg=typer.colors.RED,
        err=True,
    )
    error_collection.append(item)
    return False


def main(
        base_dir: Path = "",
        storage_dir: Path = "",
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
    operation_complete = Event()
    operation_failed = Event()

    if not storage_dir:
        storage_dir = base_dir

    worker_pool = ThreadPoolScheduler(3)
    failed_results: List[FailedTarget] = []

    # Use this to pull errors out of the stream.
    failed_record_filter = partial(filter_errors, error_collection=failed_results)

    # Identify targets
    file_listing_shared = get_files(base_dir, filter_regex, worker_pool).pipe(
        operators.filter(failed_record_filter),
        operators.publish(),
    )

    # Load targets from disk
    loaded_files = load_file_content(file_listing_shared).pipe(
        operators.filter(failed_record_filter),
    )

    enriched_files = loaded_files.pipe(
        generate_file_metadata,
        operators.filter(failed_record_filter),
        generate_image_metadata,
        operators.filter(failed_record_filter),
    )
    #  hashed_files = generate_file_metadata(file_listing)
    #  files_with_metadata = generate_image_metadata(hashed_files)

    files_with_move_path = generate_move_path(enriched_files, storage_dir).pipe(
        operators.filter(failed_record_filter),
    )

    if dry_run:
        files_with_move_path.subscribe(
            on_next=dry_run_print,
            on_error=lambda err: handle_error(err, operation_failed),
            on_completed=operation_complete.set,
        )

        file_listing_shared.connect()

        while not any((operation_complete.is_set(), operation_failed.is_set())):
            typer.echo("Waiting for processing to complete.", err=True)
            sleep(1)

        typer.echo(f"Encountered {len(failed_results)} Records that failed to process:")
        for fail in failed_results:
            typer.secho(fail, fg=typer.colors.RED)

        typer.echo("Operation completed.")

        return

    moved_files = files_with_move_path.pipe(
        operators.map(lambda target: fo.migrate_file_target(target, copy_only)),
        operators.filter(failed_record_filter),
        operators.map(fo.clear_empty_directories),
        operators.filter(failed_record_filter),
    )

    moved_files.subscribe(
        on_next=lambda target: typer.echo(
            f"{'Copied' if copy_only else 'Moved'} "
            f"{target.file_path} to {target.target_move_path}.",
        ),
        on_error=lambda err: handle_error(err, operation_complete),
        on_completed=operation_complete.set,
    )

    file_listing_shared.connect()

    while not any((operation_complete.is_set(), operation_failed.is_set())):
        typer.echo("Waiting for processing to complete.", err=True)
        sleep(1)

    typer.echo("Operation completed.")

    typer.echo(f"Encountered {len(failed_results)} Records that failed to process:")
    for fail in failed_results:
        typer.secho(fail, fg=typer.colors.RED)


def entrypoint() -> None:
    """Typer launchpoint."""
    typer.run(main)


if __name__ == '__main__':
    entrypoint()
