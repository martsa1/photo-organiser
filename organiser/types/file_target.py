"""Contains the FileTarget class, which is the dataclass used to maintain working state on files."""

from dataclasses import dataclass, field
from typing import Dict, Optional

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
