# Kafka group lag aggregate monitor
This utility can currently 
1. Accept `kafka-consumer-groups` output like file from stdin and print aggregated output to stdout. 
2. ssh to a remote machine with kafka running on it, run `kafka-consumer-groups`, for multiple groups, collect the output, group by group and topic and finally print average and max lag.

Currently Tested on: Python 3.11.3 and macos

## Installation

```bash
pip install kafka-lag-monitor
```

## Run

### stdin-mode
Run the below to get a general idea of how the output would look like.
```bash
cat examples/example1.txt | kafka-lag-monitor stdin-mode
```
1. Add option -v to get verbose output
2. Try option --tablefmt psql to get tabular output just like psql. (Can try any format supported [here](https://github.com/astanin/python-tabulate#table-format))

### remote-mode
```bash
kafka-lag-monitor -v --remote ubuntu@127.0.0.1 -i ~/.ssh/key.pem --bootstrap-server 127.0.0.1:9000 --group group1 --group group2
```

## Setup locally

### Install dependancies
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip3 install poetry
poetry install
```

## TODO
1. ~~Explore using tui which can monitor lag live by recording last n entries and calculating lag increase/decrease.~~ Live TUI Created. lag increase/decrease pending.
2. Currently stdin-mode supports only one file? Look for ways to concat multiple outputs and aggregate?
3. Test cases
4. monitor locally?
5. fake lag generator for testing
6. Currently refresh interval is hardcoded. (It breaks if the refresh of data taks longer than interval. FIX IT)
7. re-use ssh connection across calls in tui-mode. (Might need major refactor)
8. Make it look better. (hello darkness (css/tcss) my old friend)
9. Ability to toggle select/deselect of kafka groups during watch mode.
