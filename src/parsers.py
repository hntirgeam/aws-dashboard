import re
import sys
from datetime import datetime, timedelta, timezone
from operator import itemgetter
from typing import Dict, List, Tuple, Union

from colorama import Back, Fore, Style
from dateutil import parser
from tabulate import tabulate

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
    """Makes happy string from sad strings (adding color)."""
    happy_string = color + sad_string + Style.RESET_ALL
    return happy_string


def td_format(td_object):
    """Because timedelta object from datetime module does not have strpftfrtftprptime function I need to use this."""
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
            strings.append(f"{period_value} {period_name}{has_s}")
    return " ".join(strings)


def sort_parsed_data(data: List[List], order_by: str, env: str, state: str, rds: bool = False) -> List[List]:
    """Sorts parsed data for both EC2 and RDS instancies."""
    filtered_data = []

    header = INSTANCES_TABLE_HEADERS if not rds else DB_INSTANCES_TABLE_HEADERS
    header_inxed_env = "Env" if not rds else "Address"

    if env != "all":
        for item in data:
            if item[header.index(header_inxed_env)].find(env) != -1:
                filtered_data.append(item)

    if state != "all":
        for item in data:
            if state.lower() in item[header.index("State")]:
                filtered_data.append(item)

    else:
        filtered_data = data

    try:
        order_key = [i.lower() for i in header].index(order_by)
    except ValueError:
        return filtered_data

    return sorted(filtered_data, key=itemgetter(order_key), reverse=True)


class EC2Service:
    """EC2 Service class that has methods to parse and show data."""

    def __init__(self, ec2, color: bool) -> None:
        self.ec2 = ec2
        self.color = color

    def parse_data(self):
        """Parses data using boto3 instance. Parses it according to settings."""
        described_instances: Dict = self.ec2.describe_instances()
        ec2_data = described_instances.get("Reservations")

        if not ec2_data:
            sys.exit(-1)
        return self._parse_api_data(ec2_data)

    def show_parsed_data(self, data: List[List], tablefmt: str, sh: bool, separ: str) -> None:
        """Prints parsed data as table or as shell-compatible string."""
        if not sh:
            header = INSTANCES_TABLE_HEADERS_FANCY if self.color else INSTANCES_TABLE_HEADERS
            print(tabulate(data, header, tablefmt=tablefmt))
            return

        for instance_data in data:
            print(f"{separ}".join(instance_data))

    def _parse_api_data(self, data: Dict) -> List[List]:
        instances_data = []
        for instances in data:
            for instance in instances.get("Instances"):
                instances_data.append(self._parse_instance_data(instance))

        return instances_data

    def _parse_instance_data(self, instance_data: Dict) -> List:
        instance_id = instance_data.get("InstanceId")

        tags = self._get_instance_tags(instance_data.get("Tags"))
        instance_name = tags.get("Name")
        instance_env = tags.get("environment")

        state_name, state_code = self._get_instance_state(instance_data.get("State"))

        correct_state_time = self._get_correct_state_key(instance_data=instance_data)
        state_time = self._get_instance_state_time(correct_state_time, state_code)

        ip_addr = instance_data.get("PublicIpAddress")
        public_ip_addr = ip_addr if ip_addr else NONE_STR

        row = [instance_name, state_name, state_time, public_ip_addr, instance_env, instance_id]

        return row

    def _get_instance_tags(self, tags: List) -> Dict[str, str]:
        parsed_tags = {"Name": NONE_STR, "environment": NONE_STR}
        for tag in tags:
            parsed_tags[tag["Key"]] = tag["Value"]

        return parsed_tags

    def _get_instance_state(self, state: dict) -> Tuple[str, int]:
        state_name = state.get("Name")
        state_code = state.get("Code")

        if self.color:
            is_on: bool = state_code == STATE_CODE_RUNNING
            state_name = make_it_shine(Fore.GREEN, state_name) if is_on else make_it_shine(Fore.RED, state_name)

        return (state_name, state_code)

    def _get_correct_state_key(self, instance_data: Dict) -> Union[str, datetime]:
        reason = instance_data.get("StateTransitionReason")
        launch_time = instance_data.get("LaunchTime")
        return launch_time if not reason else reason

    def _get_instance_state_time(self, time: datetime, state_code: int) -> str:

        if state_code == STATE_CODE_RUNNING:
            running_time: timedelta = datetime.now(timezone.utc) - time
            return td_format(running_time)

        if state_code == STATE_CODE_STOPPED:
            pattern = r"^.*\((.*)\).*$"
            match = re.search(pattern, time)
            regex_match = match.group(1)
            parsed_time = parser.parse(regex_match)
            not_running_time: timedelta = datetime.now(timezone.utc) - parsed_time
            return td_format(not_running_time)

        return "No Info"


class RDSService:
    """RDS Service class that has methods to parse and show data."""

    def __init__(self, rds, color: bool) -> None:
        self.rds = rds
        self.color = color

    def parse_data(self):
        """Parses data using boto3 instance. Parses it according to settings."""
        described_db_instances: Dict = self.rds.describe_db_instances()

        rds_data = described_db_instances.get("DBInstances")

        if not rds_data:
            sys.exit(-1)
        return self._parse_api_data(rds_data)

    def _parse_api_data(self, data: Dict) -> List[List]:
        db_instances_data = []
        for instance in data:
            db_instances_data.append(self._parse_db_instance_data(instance))

        return db_instances_data

    def show_parsed_data(self, data: List[List], tablefmt: str, sh: bool, separ: str) -> None:
        """Prints parsed data as table or as shell-compatible string."""
        if not sh:
            header = DB_INSTANCES_TABLE_HEADERS_FANCY if self.color else DB_INSTANCES_TABLE_HEADERS
            print(tabulate(data, header, tablefmt=tablefmt))
            return

        for instance_data in data:
            print(f"{separ}".join(instance_data))

    def _parse_db_instance_data(self, instance_data: Dict) -> List:
        instance_name = instance_data.get("DBClusterIdentifier", NONE_STR)
        state = self._get_db_instance_state(instance_data.get("DBInstanceStatus"))
        instance_address, instance_port = self._get_instance_endpoint(instance_data.get("Endpoint"))

        row = [instance_name, state, instance_address, str(instance_port)]
        return row

    def _get_db_instance_state(self, state: str) -> str:
        if self.color:
            is_on: bool = state == DB_STATE_RUNNING
            state = make_it_shine(Fore.GREEN, state) if is_on else make_it_shine(Fore.RED, state)
        return state

    def _get_instance_endpoint(self, endpoint_data: Dict) -> Tuple[str, int]:
        return (endpoint_data.get("Address"), endpoint_data.get("Port"))
