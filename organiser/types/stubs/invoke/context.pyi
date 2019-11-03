# Stubs for invoke.context (Python 3)

from invoke.runners import Result
from typing import Dict

class DataProxy:
    ...

class Context(DataProxy):

    def run(self, command: str, **kwargs: Dict[str, str]) -> Result:
        ...

    def sudo(self, command: str, **kwargs: Dict[str, str]) -> Result:
        ...

    @property
    def cwd(self) -> str:
        ...

    def cd(self, path: str) -> None:
        ...
