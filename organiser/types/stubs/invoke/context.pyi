# Stubs for invoke.context (Python 3)

from invoke.runners import Result
from typing import Dict, Union


class DataProxy:
    ...


class Context(DataProxy):

    def run(self, command: str, **kwargs: Union[str, int, float, bool]) -> Result:
        ...

    def sudo(self, command: str, **kwargs: Union[str, int, float, bool]) -> Result:
        ...

    @property
    def cwd(self) -> str:
        ...

    def cd(self, path: str) -> None:
        ...
