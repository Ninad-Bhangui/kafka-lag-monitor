from typing import List
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, ProgressBar
from textual.containers import ScrollableContainer
from kafka_lag_monitor.main import run_remote_commands
from kafka_lag_monitor.progress_bar import TuiProgressor

from kafka_lag_monitor.schemas import RemoteDetails
from kafka_lag_monitor.utils import parse_and_agg_kafka_outputs

# from textual.reactive import reactive

# ROWS = [
#     ("group", "topic", "partition", "lag"),
#     (4, "Joseph Schooling", "Singapore", 50.39),
#     (2, "Michael Phelps", "United States", 51.14),
#     (5, "Chad le Clos", "South Africa", 51.14),
#     (6, "László Cseh", "Hungary", 51.14),
#     (3, "Li Zhuhao", "China", 51.26),
#     (8, "Mehdy Metella", "France", 51.58),
#     (7, "Tom Shields", "United States", 51.73),
#     (1, "Aleksandr Sadovnikov", "Russia", 51.84),
#     (10, "Darren Burns", "Scotland", 51.84),
# ]


class TestApp(App):
    """A textual app to manage stopwatches"""

    remote_details: RemoteDetails
    commands: List[str]
    progressor: TuiProgressor
    table: DataTable

    # CSS_PATH = "stopwatch03.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"), ("r", "refresh", "Refresh Data")]

    # def on_button_pressed(self, event: Button.Pressed) -> None:
    #     """Event handler when button pressed"""
    #     button_id = event.button.id
    #     time_display = self.query_one(TimeDisplay)
    #     if button_id == "start":
    #         time_display.start()
    #         self.add_class("started")
    #     elif button_id == "stop":
    #         time_display.stop()
    #         self.remove_class("started")
    #     elif button_id == "reset":
    #         time_display.reset()

    def compose(self) -> ComposeResult:
        """Create child widgets for app"""
        self.progressor = TuiProgressor(len(self.commands))
        self.table = DataTable()
        self.table.add_columns("group", "topic", "partition", "lag_mean", "lag_max")
        yield Header()
        yield Footer()
        # TODO: Read about textual workers, have to run progress bar and refresh concurrently to make it work properly
        # https://github.com/Textualize/textual/discussions/3135
        # https://textual.textualize.io/guide/workers/
        yield ScrollableContainer(self.progressor.progress_bar, self.table, id="layout")

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_refresh(self) -> None:
        self._refresh_data()

    def on_mount(self) -> None:
        pass
        # self._refresh_data()
    def _refresh_data(self):
        command_outputs = run_remote_commands(
            self.remote_details, self.commands, False, self.progressor
        )
        df = parse_and_agg_kafka_outputs(command_outputs)
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
        # table.add_rows(df.itertuples(index=False))


if __name__ == "__main__":
    app = TestApp()
    app.run()
