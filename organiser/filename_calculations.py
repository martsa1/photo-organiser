import re
from pathlib import Path
from typing import Optional

import pendulum


def identify_move_path(
        current_path: str,
        output_dir: str,
        file_datestamp: pendulum.DateTime,
) -> str:
    """Attempt to identify the directory (and potentially filename), to which a
    filepath should be relocated to.

    This method is opinionated, and adheres to the following logic:
    - The desired outcome is to sort inbound files into the output base
      directory, sorted into subfolders by year and month.  Files should
      finally default to being sorted into folders with a yyyy.mm folder,
      matching the files metadata. e.g. an image taken on 2019/02/03 should end
      up in /output_dir/2019/02/2019.02.03/ .
    - If the file is within a subdirectory (or multiple), if the final
      directory before the file name can be parsed as years/months, use them
      over the metadata in the output directory, any other logic still applies.
    - If the file is within a directory that contains a valid date (yyyy/mm/dd
      or yyyy.mm.dd) AND also contains other string text, this is likely an
      album I have already organised, thus we should preserve that album as is.
      e.g. a file in /base_dir/2019.01.02 something interesting/file, should
      return an output_dir of /output_dir/2019/01/2019.01.02 something
      interesting/ .

    Args:
        current_path (str): The absolute path to the current file.
        output_dir (str): The absolute pate to the base directory to which we
            should be storing processed files.
        file_datestamp (pendulum.DateTime): The datestamp representing when the
            file was created, to be used for organising where the file should
            be stored.
        date_regex (str): A Regex to use instead of the default date
            formatting that we use in this function.

    Returns: An absolute file path for the provided input path, that represents
        where the file should end up.
    """
    date_regex: str = (
        r'^(?:(?:(?P<year>\d{4})'
        r'[.-_])?'
        r'(?P<month>\d{1,2})[.-_]?) '
        r'?(?P<album_name>.*?) ?$'
    )

    working_file_path = Path(current_path)

    album_match_regex = (
        r"(?P<year>\d{4})[._-](?P<month>\d{1,2})(?:[.-_](?P<day>\d{1,2}))?\s*(?P<album>.*)/.+$"
    )
    album_match = re.search(album_match_regex, current_path)

    album_name: Optional[str] = None
    if album_match and album_match.groups():
        album_name = album_match.groupdict().get("album", None)

    target_path = Path(output_dir) / file_datestamp.format("YYYY") / file_datestamp.format("MM")

    if album_name:
        target_path = target_path / "{timestamp} {album_name}".format(
            timestamp=file_datestamp.format("YYYY.MM"), album_name=album_name
        )

    return str(
        target_path / "{}_{}".format(file_datestamp.format("YYYY.MM.DD"), working_file_path.name)
    )
