"""Work around for invoke tasks not supporting type annotations.

See https://github.com/pyinvoke/invoke/issues/357 for details.

This entire module should be removed once the above issue is resolved.
"""
from inspect import ArgSpec, getfullargspec
from typing import Any, Callable, Dict, List, Tuple, Type
from unittest.mock import patch

import invoke


# Attempt to allow invoke tasks to use type annotations in function definitions.
def fix_annotations() -> None:
    """
    Patch invoke signature handling to support type annotations.

    Pyinvoke doesnt accept annotations by default, this fix that
    Based on: https://github.com/pyinvoke/invoke/pull/606
    SOURCE: https://github.com/pyinvoke/invoke/issues/357#issuecomment-583851322


    Given that this code works with creating signatures of functions,
    explicitly, they must support Any function signatures, thus this module has
    been explicitly allowed to use the Any type in the mypy configuration.
    """
    task_argspec_annotation = Callable[
        [Callable[[Type[Any], Any], Any]],
        Tuple[List[str], Dict[str, str]],
    ]

    def patched_inspect_getargspec(func: Callable[[Any], ArgSpec]) -> ArgSpec:
        spec = getfullargspec(func)

        return ArgSpec(
            args=spec.args,
            varargs=spec.varargs or "",
            keywords=spec.varkw or "",
            defaults=spec.defaults or (),
        )

    org_task_argspec: task_argspec_annotation = getattr(invoke.tasks.Task, "argspec")

    def patched_task_argspec(self, func: Callable[[Any], Any]) -> Tuple[List[str], Dict[str, str]]:
        with patch(target="inspect.getargspec", new=patched_inspect_getargspec):
            return org_task_argspec(self, func)

    setattr(invoke.tasks.Task, "argspec", patched_task_argspec)
