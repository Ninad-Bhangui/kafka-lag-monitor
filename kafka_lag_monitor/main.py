import sys
from typing import Annotated
from tabulate import tabulate
import typer
from kafka_lag_monitor.schemas import RemoteDetails
from kafka_lag_monitor.utils import create_commands, parse_and_agg_kafka_outputs, parse_remote
from typing import List
import paramiko
from rich.progress import track, Progress
from rich import print
from rich.console import Console

err_console = Console(stderr=True)

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
):
    commands = create_commands(groups, bootstrap_server)
    remote_details = parse_remote(remote, key_filename)
    command_outputs = run_remote_commands(remote_details, commands, verbose)
    df = parse_and_agg_kafka_outputs(command_outputs)

    print(tabulate(df, headers="keys", tablefmt=tablefmt, showindex=False))


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

def run_remote_commands(remote_details: RemoteDetails, commands: List[str], verbose=False):
    print(remote_details)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    outputs = []
    try:
        ssh.connect(
            remote_details.hostname,
            username=remote_details.username,
            key_filename=remote_details.key_filename,
        )
        with Progress() as progress:
            if verbose:
                task = progress.add_task("Fetching kafka output...", total=len(commands))
            for command in commands:
                _, stdout, stderr = ssh.exec_command(command)
                errors = stderr.readlines()
                output = stdout.readlines()
                outputs.append(output)
                if verbose:
                    progress.update(task, advance=1, description=f"Running {command}")
                if errors:
                    raise Exception(errors)
            return outputs
    except Exception as e:
        err_console.print(f"Error: {e}")
        raise
    finally:
        ssh.close()