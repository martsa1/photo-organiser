"""Contains methods used to move/copy a FileTarget from its old to new location."""

import logging
import os.path
import pathlib
import re
import shutil
from typing import Union

import typer

from organiser.types import FailedTarget, FileTarget

LOG = logging.getLogger(__name__)


def _check_existing_target_file(target: FileTarget) -> FileTarget:
    """Checks for the existence of a target_move_path, increments target_move_path if so."""
    existing_file_check_regex = (
        r"(?P<base>^.*/)?(?P<file_name>[\w\d.]+)(?:\((?P<rep>\d+)\))?\.(?P<ext>.+)$"
    )

    if target.file_path == target.target_move_path:
        LOG.debug("Target file appears to already be in the correct place.")
        return target

    if os.path.isfile(target.target_move_path):
        current_file_match = re.search(existing_file_check_regex, target.target_move_path)
        if not current_file_match:
            raise ValueError("Failed to match on move target. Something bad happened!")

        match_groups = current_file_match.groupdict()

        rep = match_groups.get("rep")
        rep_count = int(rep) if rep else 0

        new_file_name = (
            "{f_name}({rep}).{ext}".format(
                f_name=match_groups.get('file_name'),
                rep=str(rep_count + 1),  # This is to ensure we always increment.
                ext=match_groups.get('ext'),
            )
        )
        target.target_move_path = os.path.join(
            match_groups.get('base', ''),
            new_file_name,
        )

        # Check that the updated target doesn't also exist
        return _check_existing_target_file(target)

    return target


def _ensure_target_directory(target_move_path: str) -> None:
    """Ensures the parent directory for target_move_path exists."""
    if not os.path.isdir(os.path.dirname(target_move_path)):
        target_dir = pathlib.Path(os.path.dirname(target_move_path))
        target_dir.mkdir(parents=True, exist_ok=True)


def migrate_file_target(target: FileTarget, copy: bool = False) -> FileTarget:
    """Apply a move, or copy of the FileTarget from source to new destination."""
    _ensure_target_directory(target.target_move_path)
    target = _check_existing_target_file(target)

    if target.file_path == target.target_move_path:
        typer.secho("File already correctly located.", fg=typer.colors.BLUE, err=True)
        return target

    if copy:
        shutil.copy(target.file_path, target.target_move_path)

    else:
        shutil.move(target.file_path, target.target_move_path)

    target.operation_complete = True

    return target


def clear_empty_directories(item: FileTarget) -> Union[FileTarget, FailedTarget]:
    """Recurse up the directory tree, remove any empty directories we find."""
    location = (pathlib.Path(item.file_path).resolve() / "..").absolute().resolve()

    while location.absolute() != pathlib.Path("/"):
        try:
            location.rmdir()
            typer.secho(f"Removed {location} as it was empty.", fg=typer.colors.BLUE)
        except OSError as err:
            if err.errno == 39:  # Directory not empty error.
                # Found a directory with stuff in it...
                LOG.info(
                    "Not deleting %s as it wasn't empty: %s.",
                    location,
                    os.listdir(location),
                )
                return item

        location = (location / "..").resolve().absolute()

    # Somehow found the top of the tree..?
    return item
