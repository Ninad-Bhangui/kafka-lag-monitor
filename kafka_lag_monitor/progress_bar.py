from rich.progress import Progress, TaskID
from abc import ABC
from typing import List, Optional, Type
from types import TracebackType


class Progressor(ABC):
    def __enter__(self):
        pass

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        pass

    def advance(self):
        pass


class DummyProgressor(Progressor):
    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        pass

    def advance(self):
        pass


class CliProgressor(Progressor):
    task_name: str
    commands: List[str]
    progressor: Progress
    task: TaskID
    counter = 0

    def __init__(self, task_name: str, commands: List[str]) -> None:
        self.task_name = task_name
        self.commands = commands

    def __enter__(self):
        self.progressor = Progress()
        self.progressor.start()
        self.task = self.progressor.add_task(self.task_name, total=len(self.commands))
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        self.progressor.stop()

    def advance(self):
        self.progressor.update(
            self.task, advance=1, description=f"Running {self.commands[self.counter]}"
        )
        self.counter += 1


# with Progress() as progress:
#             if verbose:
#                 task = progress.add_task("Fetching kafka output...", total=len(commands))
#             for command in commands:
#                 _, stdout, stderr = ssh.exec_command(command)
#                 errors = stderr.readlines()
#                 output = stdout.readlines()
#                 outputs.append(output)
#                 if verbose:
#                     progress.update(task, advance=1, description=f"Running {command}")
#                 if errors:
#                     raise Exception(errors)
#             return outputs
#
