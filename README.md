# Kafka group lag aggregate monitor
This utility will currently ssh to a remote machine with kafka running on it, run `kafka-consumer-groups`, for multiple groups, collect the output, group by group and topic and finally print average and max lag.

Currently Tested on: Python 3.11.3

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python monitor.py -v --remote ubuntu@127.0.0.1 -i ~/.ssh/key.pem --bootstrap-server 127.0.0.1:9000 --groups group1 group2
```

## TODO
1. Explore using tui which can monitor lag live by recording last n entries and calculating lag increase/decrease.
2. It need not be coupled with ssh (paramiko library) and can actually use subprocess to run `kafka-consumer-groups` locally / sdk maybe?