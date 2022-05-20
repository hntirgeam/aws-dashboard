import re
from datetime import datetime, timedelta, timezone
from pprint import pp
from typing import Any, Dict, List, Tuple, Union

import boto3
import click
from colorama import Fore, Style
from colorama import init as windows_color_init
from dateutil import parser
from tabulate import tabulate

windows_color_init()  # He he...

STATE_CODE_STOPPED = 80
STATE_CODE_RUNNING = 16

INSTANCES_TABLE_HEADERS = ("Name", "State", "State Time", "Public IP", "Env")


def make_it_shine(color, sad_string) -> str:
    happy_string = color + sad_string + Style.RESET_ALL
    return happy_string


def get_instance_tags(tags: List) -> Dict[str, str]:
    parsed_tags = {"Name": None, "environment": None}
    for tag in tags:
        parsed_tags[tag["Key"]] = tag["Value"]

    return parsed_tags


def get_instance_state(state: dict) -> Tuple[str, int]:
    state_name = state.get("Name")
    state_code = state.get("Code")

    # TODO: if color or smth
    on: bool = True if state_code == STATE_CODE_RUNNING else False
    state_name = make_it_shine(Fore.GREEN, state_name) if on else make_it_shine(Fore.RED, state_name)

    return (state_name, state_code)


def _get_correct_state_key(instance_data: Dict) -> Union[str, datetime]:
    reason = instance_data.get("StateTransitionReason")
    launch_time = instance_data.get("LaunchTime")
    return launch_time if not reason else reason


def td_format(td_object):
    seconds = int(td_object.total_seconds())
    periods = [
        ("day", 60 * 60 * 24),
        ("hour", 60 * 60),
        ("minute", 60),
    ]
    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            has_s = "s" if period_value > 1 else ""
            strings.append("%s %s%s" % (period_value, period_name, has_s))
    return " ".join(strings)


def get_instance_state_time(time: datetime, state_code: int) -> str:

    if state_code == STATE_CODE_RUNNING:
        running_time: timedelta = datetime.now(timezone.utc) - time
        return td_format(running_time)

    elif state_code == STATE_CODE_STOPPED:
        pattern = r"^.*\((.*)\).*$"
        match = re.search(pattern, time)
        regex_match = match.group(1)
        parsed_time = parser.parse(regex_match)
        not_running_time: timedelta = datetime.now(timezone.utc) - parsed_time
        return td_format(not_running_time)

    return "No Info"


def parse_instance_data(instance_data: Dict) -> List:
    tags = get_instance_tags(instance_data.get("Tags"))
    instance_name = tags.get("Name")
    instance_env = tags.get("environment")

    state_name, state_code = get_instance_state(instance_data.get("State"))

    correct_state_time = _get_correct_state_key(instance_data=instance_data)
    state_time = get_instance_state_time(correct_state_time, state_code)
    ip_addr = instance_data.get("PublicIpAddress")
    public_ip_addr = ip_addr if ip_addr else "None"

    row = [instance_name, state_name, state_time, public_ip_addr, instance_env]

    return row


def parse_api_data(data: Dict) -> List[List]:
    instances_data = []
    for instances in data:
        for instance in instances.get("Instances"):
            instances_data.append(parse_instance_data(instance))

    return instances_data


def show_parsed_data(data: List[List]) -> None:
    print(tabulate(data, INSTANCES_TABLE_HEADERS, tablefmt="psql"))


if __name__ == "__main__":
    ec2 = boto3.client("ec2")
    rds = boto3.client("rds")

    described_instances: Dict = ec2.describe_instances()
    ec2_data = described_instances.get("Reservations")

    if ec2_data:
        parsed_data = parse_api_data(ec2_data)
        show_parsed_data(parsed_data)
