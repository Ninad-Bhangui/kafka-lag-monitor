import pandas as pd
from kafka_lag_monitor.schemas import KafkaEntry, RemoteDetails
from typing import List
import paramiko
from rich.console import Console
from kafka_lag_monitor.progress_bar import DummyProgressor, Progressor
from concurrent.futures import ThreadPoolExecutor

err_console = Console(stderr=True)


def parse_and_agg_kafka_outputs(outputs):
    df = pd.DataFrame()
    for output in outputs:
        kafka_entries = parse_kafka_output(output)
        single_df = aggregate_kafka_output(kafka_entries)
        df = pd.concat([df, single_df])
    return df.sort_values(by="lag_mean", ascending=False)


def parse_kafka_output(output):
    kafka_entries: List[KafkaEntry] = []
    for line in output[2:]:
        entry = line.split()
        kafka_entries.append(
            KafkaEntry(
                group=entry[0], topic=entry[1], partition=entry[2], lag=int(entry[5])
            )
        )
    return kafka_entries


def aggregate_kafka_output(kafka_entries):
    df = pd.DataFrame(kafka_entries)
    agg_df = (
        df[["group", "topic", "partition", "lag"]]
        .groupby(by=["group", "topic"])
        .agg({"partition": "count", "lag": ["mean", "max"]})
    )
    agg_df.columns = [f"{x}_{y}" for x, y in agg_df.columns]
    agg_df.reset_index(inplace=True)
    return agg_df


def create_commands(groups: List[str], bootstrap_server: str):
    commands = [
        f"kafka-consumer-groups --bootstrap-server {bootstrap_server} --describe --group {group}"
        for group in groups
    ]
    return commands


def parse_remote(remote: str, keyfile: str) -> RemoteDetails:
    if "@" in remote:
        [username, hostname] = remote.split("@")
        return RemoteDetails(username=username, hostname=hostname, key_filename=keyfile)
    else:
        raise Exception(
            "Invalid remote, should be of the format username@ip-address, example ubuntu@127.0.0.1"
        )


def run_remote_commands(
    remote_details: RemoteDetails,
    commands: List[str],
    verbose=False,
    progress: Progressor = DummyProgressor(),
):
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
        with progress:
            for command in commands:
                _, stdout, stderr = ssh.exec_command(command)
                errors = stderr.readlines()
                output = stdout.readlines()
                outputs.append(output)
                progress.advance()
                if errors:
                    raise Exception(errors)
            return outputs
    except Exception as e:
        # err_console.print(f"Error: {e}")
        raise
    finally:
        ssh.close()


def run_remote_commands_concurrently(
    remote_details: RemoteDetails,
    commands: List[str],
    verbose=False,
    progress: Progressor = DummyProgressor(),
):
    if verbose:
        print(remote_details)
    with progress:
        with ThreadPoolExecutor() as executors:
            if verbose:
                print(f"max workers: {executors._max_workers}")
            outputs = list(
                executors.map(
                    run_single_remote_command,
                    [remote_details] * len(commands),
                    commands,
                    [verbose] * len(commands),
                    [progress] * len(commands),
                )
            )
    return outputs


def run_single_remote_command(
    remote_details: RemoteDetails,
    command: str,
    verbose=False,
    progress: Progressor = DummyProgressor(),
):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(
            remote_details.hostname,
            username=remote_details.username,
            key_filename=remote_details.key_filename,
        )
        _, stdout, stderr = ssh.exec_command(command)
        errors = stderr.readlines()
        output = stdout.readlines()
        progress.advance()
        if errors:
            raise Exception(errors)
        return output

    except Exception as e:
        raise
    finally:
        ssh.close()
