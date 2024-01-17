from collections import namedtuple
import paramiko
from typing import List
import pandas as pd
from tabulate import tabulate
import logging
import sys
import argparse

KafkaEntry = namedtuple("KafkaEntry", "group topic partition lag")
RemoteDetails = namedtuple("RemoteDetails", "username hostname key_filename")

def build_parser():
    parser = argparse.ArgumentParser(
        prog="kafka-group-lag-aggregate-monitor",
        description="Aggregates lag across multiple groups over a remote server",
    )
    parser.add_argument(
        "--remote",
        help="Kafka remote Host details Can be of the format ubuntu@127.0.0.1",
        required=True
    )
    parser.add_argument(
        "-i", "--key-filename", help="private key path. (Used with --remote)",
        required=True
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Verbose",
        default=False,
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--tablefmt",
        help="Format of output (Default: plain), other options are tabulate tablefmt options",
        default="plain",
    )
    parser.add_argument("--groups", help="Comma seperated list of kafka groups", nargs="+", required=True)
    parser.add_argument("--bootstrap-server", help="Kafka bootstrap server", required=True)
    return parser

def parse_remote(remote: str, keyfile: str) -> RemoteDetails:
    if "@" in remote:
        [username, hostname] = remote.split("@")
        return RemoteDetails(username=username, hostname=hostname, key_filename=keyfile)
    else:
        raise Exception("Invalid remote, should be of the format username@ip-address, example ubuntu@127.0.0.1")

def setup_logger(verbose=False):
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s :: %(levelname)s :: %(module)s -> %(funcName)s :: %(message)s",
    )





def combine_kafka_outputs(outputs):
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
        df[["group", "topic", "lag"]]
        .groupby(by=["group", "topic"])
        .agg(["mean", "max"])
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


# @timeit
def run_remote_commands(remote_details: RemoteDetails, commands: List[str]):
    print(remote_details)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    outputs = []
    try:
        ssh.connect(
            remote_details.hostname, username=remote_details.username, key_filename=remote_details.key_filename
        )
        for command in commands:
            logging.info(f"running command {command}")
            _, stdout, stderr = ssh.exec_command(command)
            errors = stderr.readlines()
            output = stdout.readlines()
            outputs.append(output)
            if errors:
                raise Exception(errors)
            # print(output)
        return outputs
    except Exception as e:
        logging.error(f"Error: {e}")
        raise
    finally:
        ssh.close()


def main():
    parser = build_parser()
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        parser.exit()
    print(args)
    setup_logger(args.verbose)
    logging.info("Starting")
    # Live run
    commands = create_commands(args.groups, args.bootstrap_server)
    remote_details = parse_remote(args.remote, args.key_filename)
    command_outputs = run_remote_commands(remote_details, commands)
    df = combine_kafka_outputs(command_outputs)

    # Local testing
    # file_list = ["example1.txt", "example2.txt"]
    # df = pd.DataFrame()
    # command_outputs = []
    # for filename in file_list:
    #     with open(filename) as fp:
    #         lines = fp.readlines()
    #         command_outputs.append(lines)
    # df = combine_kafka_outputs(command_outputs)

    # This is final output to stdout, this is the only place to use print. Use loggers everywhere else
    print(tabulate(df, headers="keys", tablefmt="plain", showindex=False))


if __name__ == "__main__":
    main()
