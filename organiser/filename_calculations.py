import re
from pathlib import Path
from typing import Dict, Optional

import pendulum

from organiser.types import FileTarget


def identify_photo_move_path(
        output_dir: str,
        file_target: FileTarget,
) -> FileTarget:
    """
    Attempt to identify the directory to which a FileTarget should be relocated to.

    This method is opinionated, and adheres to the following logic:

    * The desired outcome is to sort inbound files into the output base
      directory, sorted into subfolders by year and month.  Files should
      finally default to being sorted into folders with a yyyy.mm folder,
      matching the files metadata. e.g. an image taken on 2019/02/03 should end
      up in /output_dir/2019/02/2019.02.03/ .
    * If the file is within a subdirectory (or multiple), if the final
      directory before the file name can be parsed as years/months, use them
      over the metadata in the output directory, any other logic still applies.
    * If the file is within a directory that contains a valid date (yyyy/mm[/dd]
      or yyyy.mm[.dd]) AND also contains other string text, this is likely an
      album I have already organised, thus we should preserve that album as is.
      e.g. a file in /base_dir/2019.01.02 something interesting/file, should
      return an output_dir of /output_dir/2019/01/2019.01.02 something
      interesting/ .

    Args:
        output_dir: The absolute path to the base directory to which we
            should be storing processed files.

        file_target: The FileTarget to work with

    Returns: Updated FileTarget containing a target_file_path attribute
        provided the calculated value here.
    """
    if not file_target.datestamp:
        raise ValueError(
            f"Cannot determine appropriate storage location for {file_target.file_path}"
            f" without a datestamp.",
        )

    working_file_path = Path(file_target.file_path)

    working_file_datestamp = file_target.datestamp

    album_match_regex = (
        r"(?P<year>\d{4})"
        r"[._-]"
        r"(?P<month>\d{1,2})"
        r"(?:[.-_](?P<day>\d{1,2}))"
        r"?\s*(?P<album>.*)/.+$"
    )
    album_match = re.search(album_match_regex, str(working_file_path))

    regex_results: Optional[Dict[str, str]] = None
    if album_match and album_match.groups():
        regex_results = album_match.groupdict()

    # Year & Month file prefix.
    if regex_results and all((regex_results.get("year"), regex_results.get("month"))):
        target_path = Path(output_dir) / regex_results["year"] / regex_results["month"]
    else:
        target_path = Path(output_dir) / working_file_datestamp.format(
            "YYYY",
        ) / working_file_datestamp.format("MM")

    # Handle Album name, if we have one
    if regex_results and regex_results.get("album"):
        target_path = (
            target_path / f"{working_file_datestamp.format('YYYY.MM')} {regex_results['album']}"
        )

    #  final_file_name = f"{working_file_datestamp.format('YYYY.MM.DD')}_{working_file_path.name}"
    #  final_file_name = final_file_name.replace("__", "_")
    final_file_name = working_file_path.name

    file_target.target_move_path = str(target_path / final_file_name)

    return file_target
