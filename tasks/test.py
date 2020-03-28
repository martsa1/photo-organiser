"""Automation around how to run tests for the project."""

from typing import Optional

from invoke import Context, task


@task
def unit_test(
        context: Context,
        report: str = 'html',
        verbose: bool = True,
        k: Optional[str] = None,
        pdb: Optional[bool] = False,
) -> None:
    """Run pytest against the codebase, along with the code coverage plugin.

    We don't use the default coverage plugin as it attempts to provide
    coverage information across the entire codebase, including test and
    non-application files.
    """
    cmd = (
        "pytest {k} {verbose} {pdb} --color=yes --cov organiser --no-cov-on-fail"
        " --cov-report={report}".format(
            k=k if k else "",
            verbose="-v" if verbose else "",
            pdb="--pdb" if pdb else "",
            report=report,
        )
    )

    context.run(cmd)
