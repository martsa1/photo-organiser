import pytest
import pendulum

from organiser import filename_calculations as fc


def test_identify_move_path() -> None:
    """Verify we create the correct basic folder path from a given photo's
    filepath and timestamp (calculated elsewhere).
    """
    sample_filepath = "IMG_4228.JPG"
    timestamp = pendulum.DateTime(year=2015, month=5, day=4)
    expected_result = "2015/05/2015.05.04_IMG_4228.JPG"

    assert fc.identify_move_path(sample_filepath, "", timestamp) == expected_result


@pytest.mark.parametrize(
    "sample_filepath, timestamp, expected_result",
    [
        (
            "2015.05.03 Curry with Mates/IMG_4228.JPG",
            pendulum.DateTime(year=2015, month=5, day=5),
            "2015/05/2015.05 Curry with Mates/2015.05.05_IMG_4228.JPG",
        ),
        (
            "some_folder/some other folder/2015.05.03 Curry with Mates/IMG_4228.JPG",
            pendulum.DateTime(year=2015, month=5, day=5),
            "2015/05/2015.05 Curry with Mates/2015.05.05_IMG_4228.JPG",
        ),
    ],
)
def test_identify_move_with_album_name(
        sample_filepath: str, timestamp: pendulum.DateTime, expected_result: str
) -> None:
    """ If we are given a filepath that includes a valid album name, preserve
    that album name in the resulting move.  Note that we should use the file
    datestamp, over any date information in the provided file path.
    """

    assert fc.identify_move_path(sample_filepath, "", timestamp) == expected_result


@pytest.mark.parametrize(
    "prefix, expected_result",
    [
        (
            "foobar",
            "foobar/2015/05/2015.05.05_IMG_4228.JPG",
        ),
        (
            "some_folder/some other folder/",
            "some_folder/some other folder/2015/05/2015.05.05_IMG_4228.JPG",
        ),
    ],
)
def test_identity_move_with_prefix(
        prefix: str,
        expected_result: str,
) -> None:
    """If we provide a prefix path, we should be given files within that prefix
    from the identify_move_path function.
    """

    sample_filepath = "IMG_4228.JPG"
    timestamp = pendulum.DateTime(year=2015, month=5, day=5)

    assert fc.identify_move_path(
        sample_filepath,
        prefix,
        timestamp,
    ) == expected_result
