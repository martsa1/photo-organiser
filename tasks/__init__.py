"""
Invoke based build automation.

isort:skip_file
"""

# TODO - Remove this patch once https://github.com/pyinvoke/invoke/issues/357 is fixed.
from tasks.patch_invoke import fix_annotations
fix_annotations()

# pylint: disable = wrong-import-position
from tasks.lint import lint
from tasks.test import unit_test
# pylint: enable = wrong-import-position


__all__ = ["lint", "unit_test"]
