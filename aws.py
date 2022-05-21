import re
from datetime import datetime, timedelta, timezone
from operator import itemgetter
from typing import Dict, List, Tuple, Union

import boto3
import click
from colorama import Back, Fore, Style
from colorama import init as windows_color_init
from dateutil import parser
from tabulate import tabulate

windows_color_init()  # He he...

STATE_CODE_STOPPED = 80
STATE_CODE_RUNNING = 16

DB_STATE_STOPPED = "stopped"
DB_STATE_RUNNING = "available"

NONE_STR = "<None>"

INSTANCES_TABLE_HEADERS = ("Name", "State", "State Time", "Public IP", "Env", "Id")
DB_INSTANCES_TABLE_HEADERS = ("Name", "State", "Address", "Port")

AVAILABLE_SORTING_RULES = INSTANCES_TABLE_HEADERS + DB_INSTANCES_TABLE_HEADERS

INSTANCES_TABLE_HEADERS_FANCY = [Fore.BLACK + Back.CYAN + h + Style.RESET_ALL for h in INSTANCES_TABLE_HEADERS]
DB_INSTANCES_TABLE_HEADERS_FANCY = [Fore.BLACK + Back.CYAN + h + Style.RESET_ALL for h in DB_INSTANCES_TABLE_HEADERS]


def make_it_shine(color, sad_string) -> str:
    happy_string = color + sad_string + Style.RESET_ALL
    return happy_string


def get_instance_tags(tags: List) -> Dict[str, str]:
    parsed_tags = {"Name": NONE_STR, "environment": NONE_STR}
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
    instance_id = instance_data.get("InstanceId")

    tags = get_instance_tags(instance_data.get("Tags"))
    instance_name = tags.get("Name")
    instance_env = tags.get("environment")

    state_name, state_code = get_instance_state(instance_data.get("State"))

    correct_state_time = _get_correct_state_key(instance_data=instance_data)
    state_time = get_instance_state_time(correct_state_time, state_code)

    ip_addr = instance_data.get("PublicIpAddress")
    public_ip_addr = ip_addr if ip_addr else NONE_STR

    row = [instance_name, state_name, state_time, public_ip_addr, instance_env, instance_id]

    return row


def get_instance_endpoint(endpoint_data: Dict) -> Tuple[str, int]:
    return (endpoint_data.get("Address"), endpoint_data.get("Port"))


def get_db_instance_state(state: str) -> str:
    on: bool = True if state == DB_STATE_RUNNING else False
    state = make_it_shine(Fore.GREEN, state) if on else make_it_shine(Fore.RED, state)
    return state


def parse_db_instance_data(instance_data: Dict) -> List:
    instance_name = instance_data.get("DBInstanceIdentifier")
    state = get_db_instance_state(instance_data.get("DBInstanceStatus"))
    instance_address, instance_port = get_instance_endpoint(instance_data.get("Endpoint"))

    row = [instance_name, state, instance_address, instance_port]
    return row


def sort_parsed_data(data: List[List], order_by: str, env: str, rds: bool = False) -> List[List]:
    filtered_data = []

    header = INSTANCES_TABLE_HEADERS if not rds else DB_INSTANCES_TABLE_HEADERS
    header_inxed = "Env" if not rds else "Address"

    if env != "all":
        for item in data:
            if item[header.index(header_inxed)].find(env) != -1:
                filtered_data.append(item)
    else:
        filtered_data = data

    try:
        order_key = [i.lower() for i in header].index(order_by)
    except ValueError:
        return filtered_data

    return sorted(filtered_data, key=itemgetter(order_key), reverse=True)


def parse_ec_2_api_data(data: Dict) -> List[List]:
    instances_data = []
    for instances in data:
        for instance in instances.get("Instances"):
            instances_data.append(parse_instance_data(instance))

    return instances_data


def parse_rds_api_data(data: Dict) -> List[List]:
    db_instances_data = []
    for instance in data:
        db_instances_data.append(parse_db_instance_data(instance))

    return db_instances_data


def show_parsed_ec2_data(data: List[List]) -> None:
    print(tabulate(data, INSTANCES_TABLE_HEADERS_FANCY, tablefmt="psql"))


def show_parsed_rds_data(data: List[List]) -> None:
    print(tabulate(data, DB_INSTANCES_TABLE_HEADERS_FANCY, tablefmt="psql"))


def status(ec2, rds, sort_by: str, env: str) -> None:
    described_instances: Dict = ec2.describe_instances()
    described_db_instances: Dict = rds.describe_db_instances()

    ec2_data = described_instances.get("Reservations")
    rds_data = described_db_instances.get("DBInstances")

    if ec2_data:
        parsed_data = parse_ec_2_api_data(ec2_data)
        parsed_data = sort_parsed_data(parsed_data, sort_by, env)
        show_parsed_ec2_data(parsed_data)
    if rds_data:
        parsed_data = parse_rds_api_data(rds_data)
        parsed_data = sort_parsed_data(parsed_data, sort_by, env, rds=True)
        show_parsed_rds_data(parsed_data)


@click.command()
@click.option("--action", default="status", help="Actions")
@click.option("--order", default="name", help="Table sorting. Options: table header lowercase (e.g. 'state name')")
@click.option("--env", default="all", help="List only instacies that match required env. Options: prod, dev, stage")
def main(*args, **kwargs):
    ec2 = boto3.client("ec2")
    rds = boto3.client("rds")

    action = kwargs.get("action")

    if action == "status":
        order_by = kwargs.get("order")
        env = kwargs.get("env")
        status(ec2, rds, order_by, env)


if __name__ == "__main__":
    main()
