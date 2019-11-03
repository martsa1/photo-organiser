"""Collection of various utilities used by the invoke tasks."""

from typing import List
from os import walk
from os.path import join, dirname, normpath
from functools import lru_cache


@lru_cache(1)
def get_project_files(exclude_tasks: bool = False, exclude_tests: bool = False) -> List[str]:
    """Get a list of all the python files in the project."""
    project_files: List[str] = []

    for root, _, files in walk(join(dirname(__file__), "../organiser")):
        for file in files:
            if any((file.endswith('.py'), file.endswith('.pyi'))):
                project_files.append(normpath(join(root, file)))

    if not exclude_tasks:
        for root, _, files in walk(join(dirname(__file__), "../tasks")):
            for file in files:
                if any((file.endswith('.py'), file.endswith('.pyi'))):
                    project_files.append(normpath(join(root, file)))

    if not exclude_tests:
        for root, _, files in walk(join(dirname(__file__), "../tests")):
            for file in files:
                if any((file.endswith('.py'), file.endswith('.pyi'))):
                    project_files.append(normpath(join(root, file)))

    return project_files
