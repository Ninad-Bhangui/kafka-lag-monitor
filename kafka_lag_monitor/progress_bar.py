from rich.progress import Progress, TaskID
from abc import ABC
from typing import List, Optional, Type
from types import TracebackType

# from textual.app import App, ComposeResult
# from textual.containers import Center, VerticalScroll
# from textual.widgets import Button, Header, Input, Label, ProgressBar
from textual.widgets import ProgressBar


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


class TuiProgressor(Progressor):
    # total: int
    progress_bar: ProgressBar

    def __init__(self, total) -> None:
        # self.total = total
        self.progress_bar = ProgressBar(total=total, show_eta=False)

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
        self.progress_bar.advance(1)
