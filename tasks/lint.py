"""Methods to provide code linting."""

from invoke import task, Context
from tasks.utils import get_project_files


@task
def lint(context):
    # type: (Context) -> None
    """Run various linters against the code base."""

    files_space_separated = " ".join(get_project_files())
    context.run("flake8 {}".format(files_space_separated), warn=True)

    context.run("mypy {}".format(files_space_separated), warn=True)

    context.run("pylint {}".format(files_space_separated), warn=True)

