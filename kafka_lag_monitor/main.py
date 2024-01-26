import sys
from typing import Annotated
from tabulate import tabulate
import typer
from kafka_lag_monitor.progress_bar import CliProgressor, DummyProgressor
from kafka_lag_monitor.utils import (
    create_commands,
    parse_and_agg_kafka_outputs,
    parse_remote,
    run_remote_commands,
    run_remote_commands_concurrently,
)
from typing import List
from rich import print
from kafka_lag_monitor.tui import TestApp
import time


app = typer.Typer()


@app.command()
def remote_mode(
    remote: Annotated[
        str,
        typer.Option(
            "--remote",
            help="Kafka remote Host details Can be of the format ubuntu@127.0.0.1",
        ),
    ],
    key_filename: Annotated[
        str, typer.Option("--key-filename", "-i", help="private key path.")
    ],
    groups: Annotated[List[str], typer.Option("--group", help="List of kafka groups")],
    bootstrap_server: Annotated[
        str, typer.Option("--bootstrap-server", help="Kafka bootstrap server")
    ],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
    tablefmt: Annotated[
        str,
        typer.Option(
            help="Format of output (Default: plain), other options are tabulate tablefmt options"
        ),
    ] = "plain",
    concurrent: Annotated[bool, typer.Option(help="Run in concurrent mode")] = False,
    watch: Annotated[bool, typer.Option("--watch")] = False,
    refresh_interval_seconds: Annotated[
        float, typer.Option("--refresh-interval")
    ] = 25.0,
):
    commands = create_commands(groups, bootstrap_server)
    remote_details = parse_remote(remote, key_filename)
    if not watch:
        start = time.time()
        if verbose:
            progressor = CliProgressor("Fetching kafka output from remote...", commands)
        else:
            progressor = DummyProgressor()

        if concurrent:
            command_outputs = run_remote_commands_concurrently(
                remote_details, commands, verbose, progressor
            )
        else:
            command_outputs = run_remote_commands(
                remote_details, commands, verbose, progressor
            )
        df = parse_and_agg_kafka_outputs(command_outputs)
        end = time.time()
        if verbose:
            print(f"Time taken: {end - start} seconds")

        print(tabulate(df, headers="keys", tablefmt=tablefmt, showindex=False))
    else:
        app = TestApp()
        app.remote_details = remote_details
        app.commands = commands
        app.refresh_interval_seconds = refresh_interval_seconds
        app.run()


@app.command()
def stdin_mode(
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
    tablefmt: Annotated[
        str,
        typer.Option(
            help="Format of output (Default: plain), other options are tabulate tablefmt options"
        ),
    ] = "plain",
):
    if verbose:
        print("Starting..")
    lines = sys.stdin.readlines()
    df = parse_and_agg_kafka_outputs([lines])

    print(tabulate(df, headers="keys", tablefmt=tablefmt, showindex=False))

    for _, row in df.iterrows():
        print(row["group"])
