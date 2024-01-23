from typing import List
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, ProgressBar
from textual.containers import ScrollableContainer
from kafka_lag_monitor.main import run_remote_commands
from kafka_lag_monitor.progress_bar import TuiProgressor
from textual import work

from kafka_lag_monitor.schemas import RemoteDetails
from kafka_lag_monitor.utils import parse_and_agg_kafka_outputs

class TestApp(App):
    """A textual app to manage stopwatches"""

    remote_details: RemoteDetails
    commands: List[str]
    progressor: TuiProgressor
    table: DataTable

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for app"""
        self.progressor = TuiProgressor(len(self.commands))
        self.table = DataTable()
        self.table.add_columns("group", "topic", "partition", "lag_mean", "lag_max")
        yield Header()
        yield Footer()
        yield ScrollableContainer(self.progressor.progress_bar, self.table, id="layout")

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_refresh(self) -> None:
        self._refresh_data()

    def on_mount(self) -> None:
        self._refresh_data()    #Initial refresh
        self.set_interval(15, self._refresh_data)    #Set interval for every 5s (TODO: Maybe configurable?)

    @work(exclusive=True, thread=True)
    def _refresh_data(self):
        self.progressor.progress_bar.update(progress=0)
        command_outputs = run_remote_commands(
            self.remote_details, self.commands, False, self.progressor
        )
        df = parse_and_agg_kafka_outputs(command_outputs)
        self.table.clear()
        for _, row in df.iterrows():
            tupled_row = (
                row["group"],
                row["topic"],
                row["partition_count"],
                row["lag_mean"],
                row["lag_max"],
            )
            self.table.add_row(
                *tupled_row, key=f"{row['group']}-{row['topic']}"
            )  # TODO: better way to convert


if __name__ == "__main__":
    app = TestApp()
    app.run()
