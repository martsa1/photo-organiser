"""Module responsible for functions that iterate through the file system."""

import base64
import logging
import os
import re
from os.path import relpath
from pathlib import Path
from typing import Iterable, Optional

import rx
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from rx import operators

from organiser.types import FileTarget

LOG = logging.getLogger(__file__)


def file_listing_iterator(
        base_dir: Optional[Path] = None,
        filename_filter: Optional[str] = None,
) -> Iterable[FileTarget]:
    """Yield FileTargets for files in the provided bsae directory, matching filename_filter."""
    if base_dir is None:
        base_dir = Path(os.path.dirname(__file__))

    for directory, _, filenames in os.walk(relpath(base_dir.absolute(), os.path.curdir)):
        for filename in filenames:
            if filename_filter:
                try:
                    matches_filter = re.search(filename_filter, filename)
                    if matches_filter:
                        target = FileTarget(os.path.join(directory, filename))
                        yield target

                except re.error as err:
                    LOG.warning(
                        "Invalid file filter provided: %s. Error: %s",
                        filename_filter,
                        err,
                    )
                    continue

            else:
                yield FileTarget(os.path.join(directory, filename))


def observable_file_list(base_dir: Optional[str] = None, filter_: str = "") -> rx.Observable:
    """Return an Observable from file listing, whilst handling directory and filter arguments."""
    return rx.from_iterable(file_listing_iterator(base_dir, filter_))


def sha256_file(file_target: FileTarget) -> FileTarget:
    """Return the SHA256 hash of the provided FileTarget."""
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(file_target.file_contents)
    file_target.file_hash = digest.finalize()

    return file_target


def b64_encode(byte_string: bytes) -> str:
    """Base 64 encode a byte string and return a unicode string."""
    b64_bytes = base64.b64encode(byte_string)

    return b64_bytes.decode("utf-8")


def encode_shasum(target: FileTarget) -> FileTarget:
    """Store sha256 hash as b64 encodedstring."""
    if target.file_hash:
        target.encoded_hash = b64_encode(target.file_hash)

    return target


def load_file_contents(file_target: FileTarget) -> FileTarget:
    """Reads the contents of FileTarget and returns updated FileTarget containing the files data."""
    try:
        with open(file_target.file_path, "rb") as file_handle:
            file_target.file_contents = file_handle.read()
            return file_target

    except OSError as err:
        LOG.warning("Failed to read content from %s", file_target.file_path)
        raise err


if __name__ == "__main__":
    file_listing = rx.from_iterable(file_listing_iterator())

    hashed_files = file_listing.pipe(
        operators.map(load_file_contents),
        operators.map(sha256_file),
        operators.map(encode_shasum),
        operators.map(lambda target: target.clear_contents_data()),
        #  operators.map(lambda file_path, file_hash: (file_path, b64_encode(file_hash))),
    )

    hashed_files.subscribe(print)
