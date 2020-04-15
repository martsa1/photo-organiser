"""Contains the FileTarget class, which is the dataclass used to maintain working state on files."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from os.path import sep

from exifread.classes import IfdTag
from pendulum import DateTime


@dataclass
class FileTarget:
    """Class used to manage state related to a file that needs organising."""
    file_path: str

    file_contents: Optional[bytes] = field(default=None)
    file_hash: Optional[bytes] = field(default=None)
    encoded_hash: Optional[str] = field(default=None)

    datestamp: Optional[DateTime] = field(default=None)

    target_move_path: str = field(default="")

    # TODO - Make an ImageFile subclass of FileTarget for use with image specific processing.
    image_metadata: Dict[str, IfdTag] = field(init=False, default_factory=dict)

    operation_complete: bool = field(init=False, default=False)

    def clear_contents_data(self) -> "FileTarget":
        """Purge the contents of the file from the instance to preserve memory."""
        self.file_contents = None

        return self

    def __str__(self) -> str:
        return (
            f"File Target:\n"
            f"   Path: {self.file_path}\n"
            f"   Hash: {self.encoded_hash}\n"
            f"   Target Path: {self.target_move_path}"
        )

    def __eq__(self, other: object) -> bool:
        """Check whether this FileTarget is a duplicate of another or not.

        Returns True if the file hashes match.

        Technically, even fi everything else is the same, the files are not
        identical,which would be likely due to an edit made to one of the files
        etc.
        """
        if not isinstance(other, FileTarget):
            return False

        if self.file_hash == other.file_hash:
            return True

        return False

    def update(self, other: "FileTarget", overwrite: bool = False) -> "FileTarget":
        """Update any attributes on self, that are provided by other.

        If overwrite is set, update even data already set on self.

        Will skip updating with other's values, if those values are also unset.

        Will never update the original file path (effectively thats our primary
        key).
        """
        excludes = ("file_path",)
        attrs = (
            attr for attr in dir(other)
            if not callable(getattr(other, attr)) and not attr.startswith("_")
        )

        for attr in attrs:
            if attr in excludes:
                continue

            other_attr = getattr(other, attr)
            if not other_attr:
                # Don't bother updating if other doesn't have a value for this attribute.
                continue

            if overwrite:
                setattr(self, attr, other_attr)

            elif not getattr(self, attr):
                setattr(self, attr, other_attr)

        return self


@dataclass
class FailedTarget():
    """Subclass of FileTarget used to track operations which failed."""

    original_record: FileTarget
    failure_reason: Exception

    def __str__(self) -> str:
        return (
            f"FailedTarget:"
            f" Original Path: {self.original_record.file_path}\n"
            f"    Reason for Failure: {self.failure_reason}"
        )
