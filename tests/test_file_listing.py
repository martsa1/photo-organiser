from typing import List

import os.path as path
import pytest
from _pytest.monkeypatch import MonkeyPatch
from unittest.mock import create_autospec

from organiser import file_listing as fl


@pytest.mark.parametrize(
    "filter, expected_result",
    [
        ("", ["test/one.py", "test/two.py", "test/three.py", "test/one.jpg"]),
        (r".*\.jpg", ["test/one.jpg"]),
        (r".*\.NONE", []),
        (r"\\\\\\", []),
    ],
)
def test_file_listing_iterator(
        filter: str,
        expected_result: List[str],
        monkeypatch: MonkeyPatch,
) -> None:
    """Verify we correctly get file lists based on provided inputs."""
    mock_walk = create_autospec(fl.os.walk)
    mock_walk.return_value = [
        ("test", (None), ("one.py", "two.py", "three.py", "one.jpg")),
    ]
    monkeypatch.setattr("organiser.file_listing.os.walk", mock_walk)

    base_dir = path.abspath(path.dirname(__file__))
    file_listing = [file.file_path for file in fl.file_listing_iterator(base_dir, filter)]

    assert file_listing == expected_result
